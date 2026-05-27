import streamlit as st
from aws_client import client


STATE_ICONS = {
    "ONLINE": "🟢", "OFFLINE": "🔴", "STARTING": "🟡",
    "STOPPING": "🟠", "START_FAILED": "🔴", "STOP_FAILED": "🔴",
}


def render():
    st.subheader("📤 Transfer — SFTP Servers")
    transfer = client("transfer")

    if "transfer_selected" not in st.session_state:
        st.session_state.transfer_selected = None

    try:
        servers = transfer.list_servers().get("Servers", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.transfer_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(servers)} SFTP server(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not servers:
            st.info("No Transfer servers found.")
            return

        for s in servers:
            sid = s["ServerId"]
            state = s.get("State", "—")
            icon = STATE_ICONS.get(state, "⚪")
            domain = s.get("Domain", "—")
            endpoint_type = s.get("EndpointType", "—")
            user_count = s.get("UserCount", 0)

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.markdown(f"**{sid}**")
            c2.caption(f"{icon} {state}")
            c3.caption(f"{domain} · {endpoint_type}")
            c4.caption(f"{user_count} user(s)")
            if c5.button("View →", key=f"transfer_btn_{sid}"):
                st.session_state.transfer_selected = sid
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    sid = st.session_state.transfer_selected
    server_summary = next((s for s in servers if s["ServerId"] == sid), None)
    if not server_summary:
        st.session_state.transfer_selected = None
        st.rerun()

    if st.button("← Back to servers"):
        st.session_state.transfer_selected = None
        st.rerun()

    try:
        server = transfer.describe_server(ServerId=sid)["Server"]
    except Exception as e:
        st.error(str(e))
        return

    state = server.get("State", "—")
    icon = STATE_ICONS.get(state, "⚪")
    st.markdown(f"### {sid}")
    st.caption(f"ARN: `{server.get('Arn', '—')}`")

    hostname = f"{sid}.server.transfer.us-east-1.amazonaws.com"
    st.code(f"sftp -i ~/.ssh/id_rsa user@{hostname}", language="bash")

    c1, c2, c3 = st.columns(3)
    c1.metric("State", f"{icon} {state}")
    c2.metric("Domain", server.get("Domain", "—"))
    c3.metric("Endpoint Type", server.get("EndpointType", "—"))

    tab1, tab2 = st.tabs(["Users", "Configuration"])

    with tab1:
        try:
            users = transfer.list_users(ServerId=sid).get("Users", [])
            if users:
                rows = [
                    {
                        "Username": u.get("UserName", "—"),
                        "Role": (u.get("Role") or "—")[-40:],
                        "Home Dir": u.get("HomeDirectory", "—"),
                        "SSH Keys": u.get("SshPublicKeyCount", 0),
                    }
                    for u in users
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No users found.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        st.dataframe([
            {"Field": "Identity Provider", "Value": server.get("IdentityProviderType", "—")},
            {"Field": "Logging Role", "Value": (server.get("LoggingRole") or "—")[-40:]},
            {"Field": "Security Policy", "Value": server.get("SecurityPolicyName", "—")},
            {"Field": "Protocols", "Value": ", ".join(server.get("Protocols", []))},
        ], use_container_width=True, hide_index=True)
