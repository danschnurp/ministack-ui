import streamlit as st
from aws_client import client


STATUS_ICON = {
    "RUNNING": "🔵", "SUCCEEDED": "🟢", "FAILED": "🔴",
    "TIMED_OUT": "🟠", "ABORTED": "⚫",
}


def render():
    st.subheader("🪜 Step Functions")
    sf = client("stepfunctions")

    try:
        machines = sf.list_state_machines().get("stateMachines", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not machines:
        st.info("No state machines found.")
        return

    if "sf_selected" not in st.session_state:
        st.session_state.sf_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.sf_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(machines)} state machine(s)")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for sm in machines:
            name = sm["name"]
            arn = sm["stateMachineArn"]
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.markdown(f"**{name}**")
            c2.caption(sm.get("type", "—"))
            c3.caption(str(sm.get("creationDate", "—"))[:10])
            if c4.button("View →", key=f"sf_btn_{name}"):
                st.session_state.sf_selected = arn
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    sm_arn = st.session_state.sf_selected
    sm = next((m for m in machines if m["stateMachineArn"] == sm_arn), None)

    if not sm:
        st.session_state.sf_selected = None
        st.rerun()

    if st.button("← Back to list"):
        st.session_state.sf_selected = None
        st.rerun()

    st.markdown(f"### {sm['name']}")

    try:
        desc = sf.describe_state_machine(stateMachineArn=sm_arn)
    except Exception as e:
        st.error(str(e))
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Type", desc.get("type", "—"))
    c2.metric("Status", desc.get("status", "—"))
    c3.metric("Created", str(desc.get("creationDate", "—"))[:10])

    with st.expander("ARN"):
        st.code(sm_arn, language="text")

    with st.expander("Definition (ASL)"):
        st.code(desc.get("definition", ""), language="json")

    # Recent executions
    st.divider()
    st.markdown("**Recent Executions**")
    try:
        executions = sf.list_executions(stateMachineArn=sm_arn, maxResults=20).get("executions", [])
        if executions:
            rows = []
            for ex in executions:
                status = ex.get("status", "—")
                icon = STATUS_ICON.get(status, "⚪")
                rows.append({
                    "Name": ex["name"],
                    "Status": f"{icon} {status}",
                    "Started": str(ex.get("startDate", "—"))[:19],
                    "Stopped": str(ex.get("stopDate", "—"))[:19] if ex.get("stopDate") else "—",
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

            # Drill into an execution
            exec_names = [e["name"] for e in executions]
            selected_exec = st.selectbox("Inspect execution", ["—"] + exec_names, key="sf_exec_select")
            if selected_exec != "—":
                exec_arn = next(e["executionArn"] for e in executions if e["name"] == selected_exec)
                try:
                    ex_desc = sf.describe_execution(executionArn=exec_arn)
                    with st.expander("Input"):
                        st.code(ex_desc.get("input", ""), language="json")
                    if ex_desc.get("output"):
                        with st.expander("Output"):
                            st.code(ex_desc["output"], language="json")
                    if ex_desc.get("error"):
                        st.error(f"Error: {ex_desc['error']} — {ex_desc.get('cause', '')}")
                except Exception as e:
                    st.error(str(e))
        else:
            st.info("No executions found.")
    except Exception as e:
        st.error(str(e))
