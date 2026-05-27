import time
import streamlit as st
from aws_client import client


STATE_ICONS = {
    "SUCCEEDED": "🟢", "FAILED": "🔴", "CANCELLED": "🟠",
    "RUNNING": "🟡", "QUEUED": "🟡",
}


def render():
    st.subheader("🔍 Athena — Interactive Query Service")
    athena = client("athena")

    tab1, tab2, tab3 = st.tabs(["Run Query", "Query History", "Data Catalogs"])

    with tab1:
        st.markdown("#### Execute SQL Query")

        try:
            wgs = athena.list_work_groups().get("WorkGroups", [])
            wg_names = [w["Name"] for w in wgs] or ["primary"]
        except Exception:
            wg_names = ["primary"]

        try:
            dcs = athena.list_data_catalogs().get("DataCatalogsSummary", [])
            catalog_names = [c["CatalogName"] for c in dcs] or ["AwsDataCatalog"]
        except Exception:
            catalog_names = ["AwsDataCatalog"]

        col1, col2 = st.columns(2)
        workgroup = col1.selectbox("Work Group", wg_names)
        catalog = col2.selectbox("Data Catalog", catalog_names)
        output_location = st.text_input("S3 Output Location", placeholder="s3://my-bucket/athena-results/")
        query = st.text_area("SQL Query", height=120, placeholder="SELECT * FROM my_table LIMIT 10;")

        if st.button("▶ Run Query", disabled=not query):
            if not output_location:
                st.warning("S3 output location is required.")
            else:
                try:
                    resp = athena.start_query_execution(
                        QueryString=query,
                        WorkGroup=workgroup,
                        QueryExecutionContext={"Catalog": catalog},
                        ResultConfiguration={"OutputLocation": output_location},
                    )
                    qid = resp["QueryExecutionId"]
                    st.info(f"Query started: `{qid}`")

                    with st.spinner("Waiting for results…"):
                        for _ in range(30):
                            time.sleep(1)
                            status_resp = athena.get_query_execution(QueryExecutionId=qid)
                            state = status_resp["QueryExecution"]["Status"]["State"]
                            if state in ("SUCCEEDED", "FAILED", "CANCELLED"):
                                break

                    icon = STATE_ICONS.get(state, "⚪")
                    st.markdown(f"**Status:** {icon} {state}")

                    if state == "SUCCEEDED":
                        results = athena.get_query_results(QueryExecutionId=qid)
                        rows = results.get("ResultSet", {}).get("Rows", [])
                        if rows:
                            headers = [c.get("VarCharValue", "") for c in rows[0].get("Data", [])]
                            data = [
                                {headers[i]: col.get("VarCharValue", "") for i, col in enumerate(row.get("Data", []))}
                                for row in rows[1:]
                            ]
                            st.dataframe(data, use_container_width=True, hide_index=True)
                        else:
                            st.info("Query returned no rows.")
                    elif state == "FAILED":
                        reason = status_resp["QueryExecution"]["Status"].get("StateChangeReason", "—")
                        st.error(f"Query failed: {reason}")
                except Exception as e:
                    st.error(f"Failed: {e}")

    with tab2:
        try:
            history = athena.list_query_executions(MaxResults=20).get("QueryExecutionIds", [])
            if history:
                execs = athena.batch_get_query_execution(QueryExecutionIds=history).get("QueryExecutions", [])
                rows = [
                    {
                        "Query ID": e.get("QueryExecutionId", "—")[:8] + "…",
                        "State": e.get("Status", {}).get("State", "—"),
                        "Database": e.get("QueryExecutionContext", {}).get("Database", "—"),
                        "Scanned (bytes)": e.get("Statistics", {}).get("DataScannedInBytes", "—"),
                        "Runtime (ms)": e.get("Statistics", {}).get("TotalExecutionTimeInMillis", "—"),
                        "Submitted": str(e.get("Status", {}).get("SubmissionDateTime", "—"))[:19],
                    }
                    for e in execs
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No recent query executions.")
        except Exception as e:
            st.error(str(e))

    with tab3:
        try:
            catalogs = athena.list_data_catalogs().get("DataCatalogsSummary", [])
            if catalogs:
                rows = [
                    {
                        "Catalog Name": c.get("CatalogName", "—"),
                        "Type": c.get("Type", "—"),
                        "Description": c.get("Description", "—"),
                    }
                    for c in catalogs
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No data catalogs found.")
        except Exception as e:
            st.error(str(e))
