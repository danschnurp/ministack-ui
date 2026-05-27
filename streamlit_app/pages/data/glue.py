import streamlit as st
from aws_client import client


STATE_ICON = {
    "SUCCEEDED": "🟢", "RUNNING": "🔵", "FAILED": "🔴",
    "STOPPED": "🟡", "STARTING": "🟡", "STOPPING": "🟡",
}


def render():
    st.subheader("🔗 Glue")
    glue = client("glue")

    tab1, tab2, tab3 = st.tabs(["Databases", "Jobs", "Crawlers"])

    with tab1:
        try:
            dbs = glue.get_databases().get("DatabaseList", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            dbs = []

        if not dbs:
            st.info("No databases found.")
        else:
            col1, col2 = st.columns([6, 1])
            col1.caption(f"{len(dbs)} database(s)")
            if col2.button("🔄 Refresh", use_container_width=True, key="glue_refresh"):
                st.rerun()

            selected_db = st.selectbox("Database", [d["Name"] for d in dbs])
            if selected_db:
                try:
                    tables = glue.get_tables(DatabaseName=selected_db).get("TableList", [])
                    st.caption(f"{len(tables)} table(s) in `{selected_db}`")
                    if tables:
                        st.dataframe([
                            {
                                "Table": t["Name"],
                                "Type": t.get("TableType", "—"),
                                "Location": t.get("StorageDescriptor", {}).get("Location", "—"),
                                "Created": str(t.get("CreateTime", "—"))[:10],
                            }
                            for t in tables
                        ], use_container_width=True, hide_index=True)
                    else:
                        st.info("No tables in this database.")
                except Exception as e:
                    st.error(str(e))

    with tab2:
        try:
            jobs = glue.get_jobs().get("Jobs", [])
        except Exception as e:
            st.error(str(e))
            jobs = []

        if not jobs:
            st.info("No jobs found.")
        else:
            if "glue_job_selected" not in st.session_state:
                st.session_state.glue_job_selected = None

            if st.session_state.glue_job_selected is None:
                st.caption(f"{len(jobs)} job(s)")
                for job in jobs:
                    name = job["Name"]
                    c1, c2, c3 = st.columns([5, 2, 1])
                    c1.markdown(f"**{name}**")
                    c2.caption(job.get("Command", {}).get("Name", "—"))
                    if c3.button("View →", key=f"glue_job_{name}"):
                        st.session_state.glue_job_selected = name
                        st.rerun()
            else:
                jname = st.session_state.glue_job_selected
                job = next((j for j in jobs if j["Name"] == jname), None)
                if not job:
                    st.session_state.glue_job_selected = None
                    st.rerun()

                if st.button("← Back to list"):
                    st.session_state.glue_job_selected = None
                    st.rerun()

                st.markdown(f"### {jname}")
                c1, c2, c3 = st.columns(3)
                c1.metric("Role", job.get("Role", "—").split("/")[-1])
                c2.metric("Type", job.get("Command", {}).get("Name", "—"))
                c3.metric("Workers", job.get("NumberOfWorkers", "—"))

                try:
                    runs = glue.get_job_runs(JobName=jname, MaxResults=10).get("JobRuns", [])
                    if runs:
                        with st.expander(f"Recent Runs ({len(runs)})"):
                            rows = []
                            for r in runs:
                                state = r.get("JobRunState", "—")
                                icon = STATE_ICON.get(state, "⚪")
                                rows.append({
                                    "Run ID": r["Id"][:16] + "…",
                                    "State": f"{icon} {state}",
                                    "Started": str(r.get("StartedOn", "—"))[:19],
                                    "Duration (s)": r.get("ExecutionTime", "—"),
                                })
                            st.dataframe(rows, use_container_width=True, hide_index=True)
                except Exception:
                    pass

    with tab3:
        try:
            crawlers = glue.get_crawlers().get("Crawlers", [])
        except Exception as e:
            st.error(str(e))
            crawlers = []

        if not crawlers:
            st.info("No crawlers found.")
        else:
            st.caption(f"{len(crawlers)} crawler(s)")
            rows = []
            for c in crawlers:
                state = c.get("State", "—")
                icon = "🟢" if state == "READY" else "🔵" if state == "RUNNING" else "🟡"
                rows.append({
                    "Crawler": c["Name"],
                    "State": f"{icon} {state}",
                    "Database": c.get("DatabaseName", "—"),
                    "Last Run": str(c.get("LastCrawl", {}).get("StartTime", "—"))[:19],
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)
