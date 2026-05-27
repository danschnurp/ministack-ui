import streamlit as st
from aws_client import client


STATUS_ICONS = {
    "CREATE_COMPLETE": "🟢", "UPDATE_COMPLETE": "🟢", "DELETE_COMPLETE": "⚫",
    "CREATE_IN_PROGRESS": "🟡", "UPDATE_IN_PROGRESS": "🟡", "DELETE_IN_PROGRESS": "🟠",
    "CREATE_FAILED": "🔴", "UPDATE_FAILED": "🔴", "DELETE_FAILED": "🔴",
    "ROLLBACK_COMPLETE": "🟠", "ROLLBACK_IN_PROGRESS": "🟠",
    "UPDATE_ROLLBACK_COMPLETE": "🟠", "REVIEW_IN_PROGRESS": "🟡",
}


def render():
    st.subheader("☁️ CloudFormation — Stacks")
    cfn = client("cloudformation")

    if "cfn_selected" not in st.session_state:
        st.session_state.cfn_selected = None

    try:
        stacks = cfn.describe_stacks().get("Stacks", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.cfn_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(stacks)} stack(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not stacks:
            st.info("No CloudFormation stacks found.")
            return

        for stack in stacks:
            sname = stack["StackName"]
            status = stack.get("StackStatus", "—")
            icon = STATUS_ICONS.get(status, "⚪")
            created = str(stack.get("CreationTime", "—"))[:10]
            desc = (stack.get("Description") or "—")[:50]

            c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
            c1.markdown(f"**{sname}**")
            c2.caption(f"{icon} {status}")
            c3.caption(f"Created: {created}")
            if c4.button("View →", key=f"cfn_btn_{sname}"):
                st.session_state.cfn_selected = sname
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    sname = st.session_state.cfn_selected
    stack = next((s for s in stacks if s["StackName"] == sname), None)
    if not stack:
        st.session_state.cfn_selected = None
        st.rerun()

    if st.button("← Back to stacks"):
        st.session_state.cfn_selected = None
        st.rerun()

    status = stack.get("StackStatus", "—")
    icon = STATUS_ICONS.get(status, "⚪")
    st.markdown(f"### {sname}")
    st.caption(f"ARN: `{stack.get('StackId', '—')}`")
    if stack.get("Description"):
        st.caption(stack["Description"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Status", f"{icon} {status}")
    c2.metric("Created", str(stack.get("CreationTime", "—"))[:10])
    c3.metric("Last Updated", str(stack.get("LastUpdatedTime", "—"))[:10])

    tab1, tab2, tab3, tab4 = st.tabs(["Resources", "Outputs", "Parameters", "Events"])

    with tab1:
        try:
            resources = cfn.list_stack_resources(StackName=sname).get("StackResourceSummaries", [])
            if resources:
                rows = [
                    {
                        "Logical ID": r.get("LogicalResourceId", "—"),
                        "Physical ID": (r.get("PhysicalResourceId") or "—")[:30],
                        "Type": r.get("ResourceType", "—"),
                        "Status": r.get("ResourceStatus", "—"),
                        "Last Updated": str(r.get("LastUpdatedTimestamp", "—"))[:19],
                    }
                    for r in resources
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No resources found.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        outputs = stack.get("Outputs", [])
        if outputs:
            rows = [
                {
                    "Key": o.get("OutputKey", "—"),
                    "Value": o.get("OutputValue", "—"),
                    "Description": o.get("Description", "—"),
                    "Export Name": o.get("ExportName", "—"),
                }
                for o in outputs
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No outputs defined.")

    with tab3:
        params = stack.get("Parameters", [])
        if params:
            rows = [
                {
                    "Key": p.get("ParameterKey", "—"),
                    "Value": p.get("ParameterValue", "—"),
                    "Use Previous": str(p.get("UsePreviousValue", False)),
                }
                for p in params
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No parameters.")

    with tab4:
        try:
            events = cfn.describe_stack_events(StackName=sname).get("StackEvents", [])[:30]
            if events:
                rows = [
                    {
                        "Timestamp": str(e.get("Timestamp", "—"))[:19],
                        "Logical ID": e.get("LogicalResourceId", "—"),
                        "Type": e.get("ResourceType", "—"),
                        "Status": e.get("ResourceStatus", "—"),
                        "Reason": (e.get("ResourceStatusReason") or "—")[:60],
                    }
                    for e in events
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No events found.")
        except Exception as e:
            st.error(str(e))
