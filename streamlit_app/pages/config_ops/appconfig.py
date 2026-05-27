import streamlit as st
from aws_client import client


def render():
    st.subheader("🚩 AppConfig — Application Configuration")
    apc = client("appconfig")

    if "apc_app_selected" not in st.session_state:
        st.session_state.apc_app_selected = None

    try:
        apps = apc.list_applications().get("Items", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── app list ───────────────────────────────────────────────────────────────
    if st.session_state.apc_app_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(apps)} application(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not apps:
            st.info("No AppConfig applications found.")
            return

        for app in apps:
            aid = app["Id"]
            name = app.get("Name", "—")
            desc = app.get("Description") or "—"

            c1, c2, c3 = st.columns([4, 4, 1])
            c1.markdown(f"**{name}**")
            c2.caption(desc[:50])
            if c3.button("View →", key=f"apc_app_{aid}"):
                st.session_state.apc_app_selected = aid
                st.rerun()
        return

    # ── app detail ─────────────────────────────────────────────────────────────
    aid = st.session_state.apc_app_selected
    app = next((a for a in apps if a["Id"] == aid), None)
    if not app:
        st.session_state.apc_app_selected = None
        st.rerun()

    if st.button("← Back to applications"):
        st.session_state.apc_app_selected = None
        st.rerun()

    st.markdown(f"### {app.get('Name', aid)}")
    if app.get("Description"):
        st.caption(app["Description"])

    tab1, tab2, tab3 = st.tabs(["Environments", "Configuration Profiles", "Deployments"])

    with tab1:
        try:
            envs = apc.list_environments(ApplicationId=aid).get("Items", [])
            if envs:
                rows = [
                    {
                        "Name": e.get("Name", "—"),
                        "State": e.get("State", "—"),
                        "Description": e.get("Description") or "—",
                        "ID": e.get("Id", "—"),
                    }
                    for e in envs
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No environments found.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        try:
            profiles = apc.list_configuration_profiles(ApplicationId=aid).get("Items", [])
            if profiles:
                rows = [
                    {
                        "Name": p.get("Name", "—"),
                        "Type": p.get("Type", "—"),
                        "Location URI": p.get("LocationUri", "—")[:50],
                        "ID": p.get("Id", "—"),
                    }
                    for p in profiles
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No configuration profiles found.")
        except Exception as e:
            st.error(str(e))

    with tab3:
        try:
            envs = apc.list_environments(ApplicationId=aid).get("Items", [])
            all_deployments = []
            for env in envs:
                eid = env["Id"]
                ename = env.get("Name", eid)
                try:
                    deps = apc.list_deployments(ApplicationId=aid, EnvironmentId=eid).get("Items", [])
                    for d in deps:
                        d["EnvironmentName"] = ename
                    all_deployments.extend(deps)
                except Exception:
                    pass

            if all_deployments:
                rows = [
                    {
                        "Environment": d.get("EnvironmentName", "—"),
                        "Deployment #": d.get("DeploymentNumber", "—"),
                        "State": d.get("State", "—"),
                        "Configuration": d.get("ConfigurationName", "—"),
                        "Started": str(d.get("StartedAt", "—"))[:19],
                        "Completed": str(d.get("CompletedAt", "—"))[:19],
                    }
                    for d in all_deployments
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No deployments found.")
        except Exception as e:
            st.error(str(e))
