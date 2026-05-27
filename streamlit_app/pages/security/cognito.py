import streamlit as st
from aws_client import client


def render():
    st.subheader("🔒 Cognito")
    cognito = client("cognito-idp")
    cognito_identity = client("cognito-identity")

    tab1, tab2 = st.tabs(["User Pools", "Identity Pools"])

    # ── User Pools ─────────────────────────────────────────────────────────────
    with tab1:
        if "cognito_pool_selected" not in st.session_state:
            st.session_state.cognito_pool_selected = None

        try:
            pools = cognito.list_user_pools(MaxResults=60).get("UserPools", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            pools = []

        if st.session_state.cognito_pool_selected is None:
            col1, col2 = st.columns([6, 1])
            col1.caption(f"{len(pools)} user pool(s)")
            if col2.button("🔄 Refresh", use_container_width=True, key="cognito_refresh"):
                st.rerun()

            if not pools:
                st.info("No user pools found.")
            else:
                for p in pools:
                    pid = p["Id"]
                    pname = p["Name"]
                    c1, c2, c3 = st.columns([4, 3, 1])
                    c1.markdown(f"**{pname}**")
                    c2.caption(f"ID: `{pid}`")
                    if c3.button("View →", key=f"cognito_pool_{pid}"):
                        st.session_state.cognito_pool_selected = pid
                        st.rerun()
        else:
            pid = st.session_state.cognito_pool_selected
            pool = next((p for p in pools if p["Id"] == pid), None)

            if st.button("← Back to pools"):
                st.session_state.cognito_pool_selected = None
                st.rerun()

            try:
                detail = cognito.describe_user_pool(UserPoolId=pid)["UserPool"]
            except Exception as e:
                st.error(str(e))
                return

            st.markdown(f"### {detail.get('Name', pid)}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Status", detail.get("Status", "—"))
            c2.metric("Users", detail.get("EstimatedNumberOfUsers", "—"))
            c3.metric("Created", str(detail.get("CreationDate", "—"))[:10])

            pool_tabs = st.tabs(["Users", "App Clients", "Details"])

            with pool_tabs[0]:
                try:
                    users = cognito.list_users(UserPoolId=pid).get("Users", [])
                    if not users:
                        st.info("No users found.")
                    else:
                        rows = [
                            {
                                "Username": u.get("Username", "—"),
                                "Status": u.get("UserStatus", "—"),
                                "Enabled": "Yes" if u.get("Enabled") else "No",
                                "Created": str(u.get("UserCreateDate", "—"))[:10],
                            }
                            for u in users
                        ]
                        st.dataframe(rows, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(str(e))

            with pool_tabs[1]:
                try:
                    clients = cognito.list_user_pool_clients(UserPoolId=pid, MaxResults=60).get("UserPoolClients", [])
                    if not clients:
                        st.info("No app clients found.")
                    else:
                        rows = [
                            {"Client Name": c.get("ClientName", "—"), "Client ID": c.get("ClientId", "—")}
                            for c in clients
                        ]
                        st.dataframe(rows, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(str(e))

            with pool_tabs[2]:
                fields = [
                    ("Pool ID", detail.get("Id", "—")),
                    ("ARN", detail.get("Arn", "—")),
                    ("MFA Config", detail.get("MfaConfiguration", "—")),
                    ("Last Modified", str(detail.get("LastModifiedDate", "—"))[:19]),
                    ("Deletion Protection", detail.get("DeletionProtection", "—")),
                ]
                st.dataframe(
                    [{"Field": f, "Value": v} for f, v in fields],
                    use_container_width=True,
                    hide_index=True,
                )

                schema = detail.get("SchemaAttributes", [])
                if schema:
                    with st.expander(f"Schema Attributes ({len(schema)})"):
                        st.dataframe(
                            [{"Name": a.get("Name"), "Type": a.get("AttributeDataType"), "Required": a.get("Required")} for a in schema],
                            use_container_width=True,
                            hide_index=True,
                        )

    # ── Identity Pools ─────────────────────────────────────────────────────────
    with tab2:
        try:
            id_pools = cognito_identity.list_identity_pools(MaxResults=60).get("IdentityPools", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            return

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(id_pools)} identity pool(s)")
        if col2.button("🔄 Refresh", use_container_width=True, key="cognito_id_refresh"):
            st.rerun()

        if not id_pools:
            st.info("No identity pools found.")
            return

        for ip in id_pools:
            c1, c2 = st.columns([5, 5])
            c1.markdown(f"**{ip.get('IdentityPoolName', '—')}**")
            c2.caption(f"ID: `{ip.get('IdentityPoolId', '—')}`")
