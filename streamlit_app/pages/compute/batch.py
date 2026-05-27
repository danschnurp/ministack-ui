import streamlit as st
from aws_client import client


STATUS_ICONS = {
    "VALID": "🟢", "INVALID": "🔴", "CREATING": "🟡",
    "UPDATING": "🟡", "DELETING": "🟠", "DELETED": "⚫",
    "ENABLED": "🟢", "DISABLED": "⚫",
}


def render():
    st.subheader("⚙️ AWS Batch")
    batch = client("batch")

    tab1, tab2, tab3 = st.tabs(["Compute Environments", "Job Queues", "Job Definitions"])

    with tab1:
        try:
            envs = batch.describe_compute_environments().get("computeEnvironments", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            envs = []

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(envs)} compute environment(s)")
        if col2.button("🔄 Refresh", key="batch_ce_refresh", use_container_width=True):
            st.rerun()

        if not envs:
            st.info("No compute environments found.")
        else:
            rows = [
                {
                    "Name": e.get("computeEnvironmentName", "—"),
                    "Type": e.get("type", "—"),
                    "State": e.get("state", "—"),
                    "Status": e.get("status", "—"),
                    "Status Reason": (e.get("statusReason") or "—")[:50],
                }
                for e in envs
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

    with tab2:
        try:
            queues = batch.describe_job_queues().get("jobQueues", [])
        except Exception as e:
            st.error(str(e))
            queues = []

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(queues)} job queue(s)")
        if col2.button("🔄 Refresh", key="batch_jq_refresh", use_container_width=True):
            st.rerun()

        if not queues:
            st.info("No job queues found.")
        else:
            for q in queues:
                qname = q.get("jobQueueName", "—")
                state = q.get("state", "—")
                status = q.get("status", "—")
                icon = STATUS_ICONS.get(state, "⚪")
                priority = q.get("priority", "—")

                with st.expander(f"{icon} **{qname}** — priority {priority}"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("State", state)
                    c2.metric("Status", status)
                    c3.metric("Priority", priority)

                    ces = q.get("computeEnvironmentOrder", [])
                    if ces:
                        st.markdown("**Compute Environments**")
                        st.dataframe(
                            [{"Order": ce.get("order"), "Compute Environment": ce.get("computeEnvironment", "—").split("/")[-1]} for ce in ces],
                            use_container_width=True,
                            hide_index=True,
                        )

    with tab3:
        try:
            jds = batch.describe_job_definitions(status="ACTIVE").get("jobDefinitions", [])
        except Exception as e:
            st.error(str(e))
            jds = []

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(jds)} active job definition(s)")
        if col2.button("🔄 Refresh", key="batch_jd_refresh", use_container_width=True):
            st.rerun()

        if not jds:
            st.info("No active job definitions found.")
        else:
            rows = [
                {
                    "Name": jd.get("jobDefinitionName", "—"),
                    "Revision": jd.get("revision", "—"),
                    "Type": jd.get("type", "—"),
                    "Status": jd.get("status", "—"),
                    "vCPUs": jd.get("containerProperties", {}).get("vcpus", "—"),
                    "Memory (MB)": jd.get("containerProperties", {}).get("memory", "—"),
                }
                for jd in jds
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
