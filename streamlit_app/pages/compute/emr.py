import streamlit as st
from aws_client import client


STATE_ICONS = {
    "RUNNING": "🟢", "WAITING": "🟡", "BOOTSTRAPPING": "🟡",
    "STARTING": "🟡", "TERMINATING": "🟠", "TERMINATED": "⚫",
    "TERMINATED_WITH_ERRORS": "🔴",
}


def render():
    st.subheader("💡 EMR — Elastic MapReduce")
    emr = client("emr")

    if "emr_selected" not in st.session_state:
        st.session_state.emr_selected = None

    try:
        clusters = emr.list_clusters().get("Clusters", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.emr_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(clusters)} cluster(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not clusters:
            st.info("No EMR clusters found.")
            return

        for c in clusters:
            cid = c["Id"]
            name = c.get("Name", "—")
            status = c.get("Status", {}).get("State", "—")
            icon = STATE_ICONS.get(status, "⚪")
            created = str(c.get("Status", {}).get("Timeline", {}).get("CreationDateTime", "—"))[:10]

            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.markdown(f"**{name}**")
            c2.caption(f"{icon} {status}")
            c3.caption(f"Created: {created}")
            if c4.button("View →", key=f"emr_btn_{cid}"):
                st.session_state.emr_selected = cid
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    cid = st.session_state.emr_selected

    if st.button("← Back to clusters"):
        st.session_state.emr_selected = None
        st.rerun()

    try:
        cluster = emr.describe_cluster(ClusterId=cid)["Cluster"]
    except Exception as e:
        st.error(str(e))
        return

    name = cluster.get("Name", "—")
    status = cluster.get("Status", {}).get("State", "—")
    icon = STATE_ICONS.get(status, "⚪")
    st.markdown(f"### {name}")
    st.caption(f"Cluster ID: `{cid}`")

    c1, c2, c3 = st.columns(3)
    c1.metric("Status", f"{icon} {status}")
    c2.metric("Release", cluster.get("ReleaseLabel", "—"))
    c3.metric("Log URI", cluster.get("LogUri", "—") or "—")

    apps = cluster.get("Applications", [])
    if apps:
        st.caption("Applications: " + "  ·  ".join(a.get("Name", "") for a in apps))

    tab1, tab2, tab3 = st.tabs(["Steps", "Instance Groups", "Bootstrap Actions"])

    with tab1:
        try:
            steps = emr.list_steps(ClusterId=cid).get("Steps", [])
            if steps:
                rows = [
                    {
                        "Name": s.get("Name", "—"),
                        "Status": s.get("Status", {}).get("State", "—"),
                        "Action on Failure": s.get("ActionOnFailure", "—"),
                        "Started": str(s.get("Status", {}).get("Timeline", {}).get("StartDateTime", "—"))[:19],
                    }
                    for s in steps
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No steps found.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        try:
            igs = emr.list_instance_groups(ClusterId=cid).get("InstanceGroups", [])
            if igs:
                rows = [
                    {
                        "Name": ig.get("Name", "—"),
                        "Role": ig.get("InstanceGroupType", "—"),
                        "Instance Type": ig.get("InstanceType", "—"),
                        "Requested": ig.get("RequestedInstanceCount", 0),
                        "Running": ig.get("RunningInstanceCount", 0),
                        "Status": ig.get("Status", {}).get("State", "—"),
                    }
                    for ig in igs
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No instance groups found.")
        except Exception as e:
            st.error(str(e))

    with tab3:
        actions = cluster.get("BootstrapActions", [])
        if actions:
            st.dataframe(
                [{"Name": a.get("Name", "—"), "Script": a.get("ScriptPath", "—")} for a in actions],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No bootstrap actions.")
