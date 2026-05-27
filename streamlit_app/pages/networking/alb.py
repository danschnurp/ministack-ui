import streamlit as st
from aws_client import client


STATE_ICONS = {
    "active": "🟢",
    "provisioning": "🟡",
    "active_impaired": "🟠",
    "failed": "🔴",
}


def render():
    st.subheader("⚖️ ALB / ELBv2 — Load Balancers")
    elb = client("elbv2")

    if "alb_selected" not in st.session_state:
        st.session_state.alb_selected = None

    try:
        lbs = elb.describe_load_balancers().get("LoadBalancers", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.alb_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(lbs)} load balancer(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not lbs:
            st.info("No load balancers found.")
            return

        for lb in lbs:
            arn = lb["LoadBalancerArn"]
            name = lb.get("LoadBalancerName", "—")
            state = lb.get("State", {}).get("Code", "—")
            icon = STATE_ICONS.get(state, "⚪")
            lb_type = lb.get("Type", "—").upper()
            dns = lb.get("DNSName", "—")

            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 3, 1])
            c1.markdown(f"**{name}**")
            c2.caption(lb_type)
            c3.caption(f"{icon} {state}")
            c4.caption(dns[:40])
            if c5.button("View →", key=f"alb_btn_{arn}"):
                st.session_state.alb_selected = arn
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    arn = st.session_state.alb_selected
    lb = next((l for l in lbs if l["LoadBalancerArn"] == arn), None)
    if not lb:
        st.session_state.alb_selected = None
        st.rerun()

    if st.button("← Back to list"):
        st.session_state.alb_selected = None
        st.rerun()

    name = lb.get("LoadBalancerName", "—")
    state = lb.get("State", {}).get("Code", "—")
    icon = STATE_ICONS.get(state, "⚪")
    st.markdown(f"### {name}")
    st.caption(f"ARN: `{arn}`")

    c1, c2, c3 = st.columns(3)
    c1.metric("State", f"{icon} {state}")
    c2.metric("Type", lb.get("Type", "—").upper())
    c3.metric("Scheme", lb.get("Scheme", "—"))

    c4, c5 = st.columns(2)
    c4.metric("DNS Name", lb.get("DNSName", "—"))
    c5.metric("Created", str(lb.get("CreatedTime", "—"))[:10])

    tab1, tab2, tab3 = st.tabs(["Listeners", "Target Groups", "Attributes"])

    with tab1:
        try:
            listeners = elb.describe_listeners(LoadBalancerArn=arn).get("Listeners", [])
            if listeners:
                rows = []
                for l in listeners:
                    actions = l.get("DefaultActions", [{}])
                    action_type = actions[0].get("Type", "—") if actions else "—"
                    rows.append({
                        "Port": l.get("Port", "—"),
                        "Protocol": l.get("Protocol", "—"),
                        "SSL Policy": l.get("SslPolicy", "—"),
                        "Default Action": action_type,
                        "Listener ARN": l.get("ListenerArn", "—")[-20:] + "…",
                    })
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No listeners found.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        try:
            tgs = elb.describe_target_groups(LoadBalancerArn=arn).get("TargetGroups", [])
            if tgs:
                rows = [
                    {
                        "Name": tg.get("TargetGroupName", "—"),
                        "Protocol": tg.get("Protocol", "—"),
                        "Port": tg.get("Port", "—"),
                        "Target Type": tg.get("TargetType", "—"),
                        "Health Check": tg.get("HealthCheckPath", "—"),
                    }
                    for tg in tgs
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No target groups found.")
        except Exception as e:
            st.error(str(e))

    with tab3:
        try:
            attrs = elb.describe_load_balancer_attributes(LoadBalancerArn=arn).get("Attributes", [])
            if attrs:
                st.dataframe(
                    [{"Key": a["Key"], "Value": a["Value"]} for a in attrs],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No attributes found.")
        except Exception as e:
            st.error(str(e))
