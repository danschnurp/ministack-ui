import streamlit as st
from aws_client import client


def render():
    st.subheader("📈 Auto Scaling — Groups")
    asg_client = client("autoscaling")

    if "asg_selected" not in st.session_state:
        st.session_state.asg_selected = None

    try:
        asgs = asg_client.describe_auto_scaling_groups().get("AutoScalingGroups", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.asg_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(asgs)} Auto Scaling group(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not asgs:
            st.info("No Auto Scaling groups found.")
            return

        for asg in asgs:
            name = asg["AutoScalingGroupName"]
            desired = asg.get("DesiredCapacity", 0)
            min_cap = asg.get("MinSize", 0)
            max_cap = asg.get("MaxSize", 0)
            instances = len(asg.get("Instances", []))
            status = asg.get("Status", "")
            icon = "🔴" if status else "🟢"

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.markdown(f"**{name}**")
            c2.caption(f"{icon} {desired}/{max_cap} instances")
            c3.caption(f"Min: {min_cap}  Max: {max_cap}")
            c4.caption(f"{instances} running")
            if c5.button("View →", key=f"asg_btn_{name}"):
                st.session_state.asg_selected = name
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    asg_name = st.session_state.asg_selected
    asg = next((a for a in asgs if a["AutoScalingGroupName"] == asg_name), None)
    if not asg:
        st.session_state.asg_selected = None
        st.rerun()

    if st.button("← Back to groups"):
        st.session_state.asg_selected = None
        st.rerun()

    st.markdown(f"### {asg_name}")
    st.caption(f"ARN: `{asg.get('AutoScalingGroupARN', '—')}`")

    c1, c2, c3 = st.columns(3)
    c1.metric("Desired", asg.get("DesiredCapacity", 0))
    c2.metric("Min", asg.get("MinSize", 0))
    c3.metric("Max", asg.get("MaxSize", 0))

    c4, c5 = st.columns(2)
    c4.metric("Health Check Type", asg.get("HealthCheckType", "—"))
    c5.metric("Health Check Grace (s)", asg.get("HealthCheckGracePeriod", "—"))

    tab1, tab2, tab3, tab4 = st.tabs(["Instances", "Scaling Policies", "Lifecycle Hooks", "Scheduled Actions"])

    with tab1:
        instances = asg.get("Instances", [])
        if instances:
            rows = [
                {
                    "Instance ID": i.get("InstanceId", "—"),
                    "AZ": i.get("AvailabilityZone", "—"),
                    "State": i.get("LifecycleState", "—"),
                    "Health": i.get("HealthStatus", "—"),
                    "Instance Type": i.get("InstanceType", "—"),
                    "Protected": str(i.get("ProtectedFromScaleIn", False)),
                }
                for i in instances
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No instances in this group.")

    with tab2:
        try:
            policies = asg_client.describe_policies(AutoScalingGroupName=asg_name).get("ScalingPolicies", [])
            if policies:
                rows = [
                    {
                        "Policy Name": p.get("PolicyName", "—"),
                        "Type": p.get("PolicyType", "—"),
                        "Adjustment Type": p.get("AdjustmentType", "—"),
                        "Scaling Adjustment": p.get("ScalingAdjustment", "—"),
                        "Cooldown (s)": p.get("Cooldown", "—"),
                    }
                    for p in policies
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No scaling policies found.")
        except Exception as e:
            st.error(str(e))

    with tab3:
        try:
            hooks = asg_client.describe_lifecycle_hooks(AutoScalingGroupName=asg_name).get("LifecycleHooks", [])
            if hooks:
                rows = [
                    {
                        "Hook Name": h.get("LifecycleHookName", "—"),
                        "Transition": h.get("LifecycleTransition", "—"),
                        "Default Result": h.get("DefaultResult", "—"),
                        "Heartbeat Timeout (s)": h.get("HeartbeatTimeout", "—"),
                    }
                    for h in hooks
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No lifecycle hooks configured.")
        except Exception as e:
            st.error(str(e))

    with tab4:
        try:
            actions = asg_client.describe_scheduled_actions(AutoScalingGroupName=asg_name).get("ScheduledUpdateGroupActions", [])
            if actions:
                rows = [
                    {
                        "Action Name": a.get("ScheduledActionName", "—"),
                        "Recurrence": a.get("Recurrence", "—"),
                        "Start Time": str(a.get("StartTime", "—"))[:19],
                        "Desired": a.get("DesiredCapacity", "—"),
                        "Min": a.get("MinSize", "—"),
                        "Max": a.get("MaxSize", "—"),
                    }
                    for a in actions
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No scheduled actions found.")
        except Exception as e:
            st.error(str(e))
