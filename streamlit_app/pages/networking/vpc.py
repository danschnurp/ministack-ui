import streamlit as st
from aws_client import client


def render():
    st.subheader("🔒 VPC")
    ec2 = client("ec2")

    try:
        vpcs = ec2.describe_vpcs().get("Vpcs", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not vpcs:
        st.info("No VPCs found.")
        return

    if "vpc_selected" not in st.session_state:
        st.session_state.vpc_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.vpc_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(vpcs)} VPC(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for vpc in vpcs:
            vid = vpc["VpcId"]
            name = next((t["Value"] for t in vpc.get("Tags", []) if t["Key"] == "Name"), "—")
            default_badge = " 🏷️ default" if vpc.get("IsDefault") else ""
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.markdown(f"**{name}**  \n`{vid}`")
            c2.caption(vpc.get("CidrBlock", "—"))
            c3.caption(f"{vpc.get('State', '—')}{default_badge}")
            if c4.button("View →", key=f"vpc_btn_{vid}"):
                st.session_state.vpc_selected = vid
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    vid = st.session_state.vpc_selected
    vpc = next((v for v in vpcs if v["VpcId"] == vid), None)

    if not vpc:
        st.session_state.vpc_selected = None
        st.rerun()

    if st.button("← Back to list"):
        st.session_state.vpc_selected = None
        st.rerun()

    name = next((t["Value"] for t in vpc.get("Tags", []) if t["Key"] == "Name"), vid)
    st.markdown(f"### {name}")

    c1, c2, c3 = st.columns(3)
    c1.metric("CIDR", vpc.get("CidrBlock", "—"))
    c2.metric("State", vpc.get("State", "—"))
    c3.metric("Default", "Yes" if vpc.get("IsDefault") else "No")

    # Subnets
    try:
        subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vid]}]).get("Subnets", [])
    except Exception:
        subnets = []

    with st.expander(f"Subnets ({len(subnets)})"):
        if subnets:
            st.dataframe([
                {
                    "Subnet ID": s["SubnetId"],
                    "CIDR": s.get("CidrBlock", "—"),
                    "AZ": s.get("AvailabilityZone", "—"),
                    "Available IPs": s.get("AvailableIpAddressCount", "—"),
                    "Public": "Yes" if s.get("MapPublicIpOnLaunch") else "No",
                }
                for s in subnets
            ], use_container_width=True, hide_index=True)
        else:
            st.info("No subnets.")

    # Security Groups
    try:
        sgs = ec2.describe_security_groups(Filters=[{"Name": "vpc-id", "Values": [vid]}]).get("SecurityGroups", [])
    except Exception:
        sgs = []

    with st.expander(f"Security Groups ({len(sgs)})"):
        if sgs:
            st.dataframe([
                {
                    "Group ID": sg["GroupId"],
                    "Name": sg.get("GroupName", "—"),
                    "Description": sg.get("Description", "—"),
                }
                for sg in sgs
            ], use_container_width=True, hide_index=True)
        else:
            st.info("No security groups.")

    # Route Tables
    try:
        rts = ec2.describe_route_tables(Filters=[{"Name": "vpc-id", "Values": [vid]}]).get("RouteTables", [])
    except Exception:
        rts = []

    with st.expander(f"Route Tables ({len(rts)})"):
        if rts:
            for rt in rts:
                rtid = rt["RouteTableId"]
                st.markdown(f"**{rtid}**")
                routes = rt.get("Routes", [])
                if routes:
                    st.dataframe([
                        {
                            "Destination": r.get("DestinationCidrBlock", r.get("DestinationPrefixListId", "—")),
                            "Target": r.get("GatewayId") or r.get("NatGatewayId") or r.get("InstanceId") or "—",
                            "State": r.get("State", "—"),
                        }
                        for r in routes
                    ], use_container_width=True, hide_index=True)
        else:
            st.info("No route tables.")

    tags = vpc.get("Tags", [])
    if tags:
        with st.expander(f"Tags ({len(tags)})"):
            st.dataframe([{"Key": t["Key"], "Value": t["Value"]} for t in tags],
                         use_container_width=True, hide_index=True)
