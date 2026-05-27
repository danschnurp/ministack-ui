import streamlit as st
from aws_client import client


STATE_ICON = {
    "running": "🟢",
    "stopped": "🔴",
    "pending": "🟡",
    "stopping": "🟠",
    "terminated": "⚫",
}


def render():
    st.subheader("🖥️ EC2")
    ec2 = client("ec2")

    try:
        resp = ec2.describe_instances()
        reservations = resp.get("Reservations", [])
        instances = [i for r in reservations for i in r.get("Instances", [])]
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not instances:
        st.info("No instances found.")
        return

    if "ec2_selected" not in st.session_state:
        st.session_state.ec2_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.ec2_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(instances)} instance(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for inst in instances:
            iid = inst["InstanceId"]
            name_tag = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), "—")
            state = inst.get("State", {}).get("Name", "—")
            icon = STATE_ICON.get(state, "⚪")
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.markdown(f"**{name_tag}**  \n`{iid}`")
            c2.caption(f"{icon} {state}")
            c3.caption(inst.get("InstanceType", "—"))
            if c4.button("View →", key=f"ec2_btn_{iid}"):
                st.session_state.ec2_selected = iid
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    iid = st.session_state.ec2_selected
    inst = next((i for i in instances if i["InstanceId"] == iid), None)

    if not inst:
        st.session_state.ec2_selected = None
        st.rerun()

    if st.button("← Back to list"):
        st.session_state.ec2_selected = None
        st.rerun()

    name_tag = next((t["Value"] for t in inst.get("Tags", []) if t["Key"] == "Name"), iid)
    state = inst.get("State", {}).get("Name", "—")
    icon = STATE_ICON.get(state, "⚪")
    st.markdown(f"### {name_tag}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("State", f"{icon} {state}")
    c2.metric("Type", inst.get("InstanceType", "—"))
    c3.metric("AZ", inst.get("Placement", {}).get("AvailabilityZone", "—"))
    c4.metric("Platform", inst.get("Platform", "Linux/UNIX"))

    with st.expander("Network"):
        st.dataframe([
            {"Field": "Private IP", "Value": inst.get("PrivateIpAddress", "—")},
            {"Field": "Public IP", "Value": inst.get("PublicIpAddress", "—")},
            {"Field": "VPC ID", "Value": inst.get("VpcId", "—")},
            {"Field": "Subnet ID", "Value": inst.get("SubnetId", "—")},
            {"Field": "Key Name", "Value": inst.get("KeyName", "—")},
        ], use_container_width=True, hide_index=True)

    with st.expander("Image & Launch"):
        st.dataframe([
            {"Field": "AMI ID", "Value": inst.get("ImageId", "—")},
            {"Field": "Launch Time", "Value": str(inst.get("LaunchTime", "—"))[:19]},
            {"Field": "Monitoring", "Value": inst.get("Monitoring", {}).get("State", "—")},
        ], use_container_width=True, hide_index=True)

    tags = inst.get("Tags", [])
    if tags:
        with st.expander(f"Tags ({len(tags)})"):
            st.dataframe([{"Key": t["Key"], "Value": t["Value"]} for t in tags],
                         use_container_width=True, hide_index=True)
