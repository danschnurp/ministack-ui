import streamlit as st
from aws_client import client


def render():
    st.subheader("🗄️ RDS Data API — Execute SQL")
    rds_data = client("rds-data")
    rds = client("rds")

    try:
        instances = rds.describe_db_instances().get("DBInstances", [])
        db_options = {
            db["DBInstanceIdentifier"]: db.get("DBInstanceArn", "")
            for db in instances
            if db.get("Engine", "").startswith(("postgres", "mysql", "aurora"))
        }
    except Exception:
        db_options = {}

    st.markdown("#### Connection")
    col1, col2 = st.columns(2)
    if db_options:
        selected_db = col1.selectbox("RDS Instance", list(db_options.keys()))
        resource_arn = db_options[selected_db]
    else:
        resource_arn = col1.text_input("Resource ARN", placeholder="arn:aws:rds:us-east-1:000000000000:cluster:mydb")

    secret_arn = col2.text_input("Secret ARN (Secrets Manager)", placeholder="arn:aws:secretsmanager:...")
    database = st.text_input("Database name", placeholder="mydb")

    tab1, tab2 = st.tabs(["Execute Statement", "Batch Execute"])

    with tab1:
        sql = st.text_area("SQL Statement", height=100, placeholder="SELECT * FROM users LIMIT 10;")
        include_result_metadata = st.checkbox("Include result metadata", value=True)

        if st.button("▶ Execute", disabled=not sql):
            if not resource_arn or not secret_arn:
                st.warning("Resource ARN and Secret ARN are required.")
            else:
                try:
                    kwargs = dict(
                        resourceArn=resource_arn,
                        secretArn=secret_arn,
                        sql=sql,
                        includeResultMetadata=include_result_metadata,
                    )
                    if database:
                        kwargs["database"] = database

                    resp = rds_data.execute_statement(**kwargs)
                    records = resp.get("records", [])
                    column_metadata = resp.get("columnMetadata", [])

                    st.success(f"Rows affected: {resp.get('numberOfRecordsUpdated', 0)}")

                    if records:
                        if column_metadata:
                            col_names = [c.get("name", f"col{i}") for i, c in enumerate(column_metadata)]
                        else:
                            col_names = [f"col{i}" for i in range(len(records[0]))]

                        rows = []
                        for rec in records:
                            row = {}
                            for i, field in enumerate(rec):
                                val = list(field.values())[0] if field else None
                                row[col_names[i] if i < len(col_names) else f"col{i}"] = val
                            rows.append(row)
                        st.dataframe(rows, use_container_width=True, hide_index=True)
                    else:
                        st.info("Statement executed. No rows returned.")
                except Exception as e:
                    st.error(f"Failed: {e}")

    with tab2:
        batch_sql = st.text_area("SQL Template", height=80, placeholder="INSERT INTO users (name, email) VALUES (:name, :email)")
        param_sets_raw = st.text_area(
            "Parameter sets (JSON array)",
            height=100,
            placeholder='[[{"name": {"stringValue": "Alice"}, "email": {"stringValue": "alice@example.com"}}]]',
        )

        if st.button("▶ Batch Execute"):
            if not resource_arn or not secret_arn or not batch_sql:
                st.warning("Resource ARN, Secret ARN, and SQL are required.")
            else:
                try:
                    import json
                    param_sets = json.loads(param_sets_raw) if param_sets_raw else [[]]
                    resp = rds_data.batch_execute_statement(
                        resourceArn=resource_arn,
                        secretArn=secret_arn,
                        sql=batch_sql,
                        parameterSets=param_sets,
                        database=database or None,
                    )
                    update_results = resp.get("updateResults", [])
                    st.success(f"Batch executed. {len(update_results)} result(s) returned.")
                    if update_results:
                        st.json(update_results)
                except Exception as e:
                    st.error(f"Failed: {e}")
