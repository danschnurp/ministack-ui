import json

import streamlit as st
from aws_client import client


def _format_schema_definition(raw: str) -> str:
    if not raw:
        return ""
    try:
        return json.dumps(json.loads(raw), indent=2)
    except (json.JSONDecodeError, TypeError):
        return raw


STATE_ICON = {
    "SUCCEEDED": "🟢", "RUNNING": "🔵", "FAILED": "🔴",
    "STOPPED": "🟡", "STARTING": "🟡", "STOPPING": "🟡",
}


def render():
    st.subheader("🔗 Glue")
    glue = client("glue")

    tab1, tab2, tab3, tab4 = st.tabs(["Databases", "Jobs", "Crawlers", "Schema Registry"])

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

    with tab4:
        try:
            registries = glue.list_registries().get("Registries", [])
        except Exception as e:
            st.error(f"Failed to load schema registries: {e}")
            registries = []

        if not registries:
            st.info("No schema registries found.")
        else:
            col_reg, col_schema, col_detail = st.columns([2, 2, 5])
            with col_reg:
                st.caption(f"{len(registries)} registry(ies)")
                registry_names = [r["RegistryName"] for r in registries]
                selected_registry = st.selectbox(
                    "Registry",
                    registry_names,
                    key="glue_schema_registry",
                )

            schemas = []
            if selected_registry:
                try:
                    schemas = glue.list_schemas(
                        RegistryId={"RegistryName": selected_registry},
                    ).get("Schemas", [])
                except Exception as e:
                    st.error(str(e))

            with col_schema:
                if schemas:
                    st.caption(f"{len(schemas)} schema(s)")
                    schema_names = [s["SchemaName"] for s in schemas]
                    selected_schema = st.selectbox(
                        "Schema",
                        schema_names,
                        key="glue_schema_name",
                    )
                else:
                    selected_schema = None
                    st.caption("No schemas in this registry.")

            with col_detail:
                if selected_registry and selected_schema:
                    try:
                        meta = glue.get_schema(
                            SchemaId={
                                "RegistryName": selected_registry,
                                "SchemaName": selected_schema,
                            },
                        )
                        st.markdown(f"**{selected_schema}** · `{meta.get('DataFormat', '—')}`")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Compatibility", meta.get("Compatibility", "—"))
                        c2.metric("Latest version", meta.get("LatestSchemaVersion", 0))
                        c3.metric("Status", meta.get("SchemaStatus", "—"))
                        st.caption(meta.get("SchemaArn", ""))

                        versions = glue.list_schema_versions(
                            SchemaId={
                                "RegistryName": selected_registry,
                                "SchemaName": selected_schema,
                            },
                        ).get("Schemas", [])
                        if versions:
                            st.markdown("**Versions**")
                            ver_rows = []
                            for v in versions:
                                ver_rows.append({
                                    "Version": v.get("VersionNumber", "—"),
                                    "Version ID": (v.get("SchemaVersionId") or "—")[:16] + "…",
                                    "Status": v.get("Status", "—"),
                                    "Created": str(v.get("CreatedTime", "—"))[:19],
                                })
                            st.dataframe(ver_rows, use_container_width=True, hide_index=True)

                            latest_id = versions[-1].get("SchemaVersionId")
                            if latest_id:
                                detail = glue.get_schema_version(SchemaVersionId=latest_id)
                                with st.expander(
                                    f"Latest definition (v{detail.get('VersionNumber', '?')})",
                                    expanded=True,
                                ):
                                    st.code(
                                        _format_schema_definition(
                                            detail.get("SchemaDefinition", ""),
                                        ),
                                        language="json",
                                    )
                        else:
                            st.info("No schema versions yet.")
                    except Exception as e:
                        st.error(str(e))
                elif selected_registry:
                    st.info("Select a schema to view details.")
