import streamlit as st
from aws_client import client


STATUS_ICONS = {
    "SUCCEEDED": "🟢", "FAILED": "🔴", "FAULT": "🔴",
    "TIMED_OUT": "🟠", "IN_PROGRESS": "🟡", "STOPPED": "⚫",
}


def render():
    st.subheader("🔨 CodeBuild — Projects & Builds")
    cb = client("codebuild")

    if "cb_selected" not in st.session_state:
        st.session_state.cb_selected = None

    try:
        project_names = cb.list_projects().get("projects", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.cb_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(project_names)} project(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not project_names:
            st.info("No CodeBuild projects found.")
            return

        projects = cb.batch_get_projects(names=project_names).get("projects", []) if project_names else []

        for p in projects:
            pname = p.get("name", "—")
            env = p.get("environment", {})
            source = p.get("source", {})
            last_modified = str(p.get("lastModified", "—"))[:10]

            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.markdown(f"**{pname}**")
            c2.caption(source.get("type", "—"))
            c3.caption(f"Modified: {last_modified}")
            if c4.button("View →", key=f"cb_btn_{pname}"):
                st.session_state.cb_selected = pname
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    pname = st.session_state.cb_selected

    if st.button("← Back to projects"):
        st.session_state.cb_selected = None
        st.rerun()

    try:
        projects = cb.batch_get_projects(names=[pname]).get("projects", [])
        if not projects:
            st.session_state.cb_selected = None
            st.rerun()
        project = projects[0]
    except Exception as e:
        st.error(str(e))
        return

    st.markdown(f"### {pname}")
    st.caption(f"ARN: `{project.get('arn', '—')}`")

    env = project.get("environment", {})
    source = project.get("source", {})
    artifacts = project.get("artifacts", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Source Type", source.get("type", "—"))
    c2.metric("Build Image", env.get("image", "—")[-40:])
    c3.metric("Compute Type", env.get("computeType", "—"))

    if source.get("location"):
        st.code(source["location"], language="text")

    tab1, tab2 = st.tabs(["Recent Builds", "Configuration"])

    with tab1:
        try:
            build_ids = cb.list_builds_for_project(projectName=pname).get("ids", [])
            builds = cb.batch_get_builds(ids=build_ids[:20]).get("builds", []) if build_ids else []
            if builds:
                rows = [
                    {
                        "Build ID": b.get("id", "—").split(":")[-1][:12] + "…",
                        "Status": b.get("buildStatus", "—"),
                        "Started": str(b.get("startTime", "—"))[:19],
                        "Duration (s)": round((b.get("endTime") - b.get("startTime")).total_seconds()) if b.get("endTime") and b.get("startTime") else "—",
                        "Initiator": b.get("initiator", "—"),
                    }
                    for b in builds
                ]
                status_col = [STATUS_ICONS.get(b.get("buildStatus", ""), "⚪") + " " + b.get("buildStatus", "—") for b in builds]
                for i, row in enumerate(rows):
                    row["Status"] = status_col[i]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No builds found for this project.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        st.dataframe([
            {"Field": "Artifact Type", "Value": artifacts.get("type", "—")},
            {"Field": "Artifact Location", "Value": artifacts.get("location", "—") or "—"},
            {"Field": "Privileged Mode", "Value": str(env.get("privilegedMode", False))},
            {"Field": "Service Role", "Value": (project.get("serviceRole") or "—")[-40:]},
            {"Field": "Timeout (min)", "Value": project.get("timeoutInMinutes", "—")},
            {"Field": "Queued Timeout (min)", "Value": project.get("queuedTimeoutInMinutes", "—")},
        ], use_container_width=True, hide_index=True)
