import streamlit as st
from aws_client import client


def render():
    st.subheader("🔑 IAM")
    iam = client("iam")

    tab1, tab2, tab3 = st.tabs(["Users", "Roles", "Policies"])

    with tab1:
        try:
            users = iam.list_users().get("Users", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            users = []

        if not users:
            st.info("No users found.")
        else:
            if "iam_user_selected" not in st.session_state:
                st.session_state.iam_user_selected = None

            if st.session_state.iam_user_selected is None:
                col1, col2 = st.columns([6, 1])
                col1.caption(f"{len(users)} user(s)")
                if col2.button("🔄 Refresh", use_container_width=True, key="iam_refresh"):
                    st.rerun()

                for u in users:
                    name = u["UserName"]
                    c1, c2, c3 = st.columns([5, 3, 1])
                    c1.markdown(f"**{name}**")
                    c2.caption(str(u.get("CreateDate", "—"))[:10])
                    if c3.button("View →", key=f"iam_user_{name}"):
                        st.session_state.iam_user_selected = name
                        st.rerun()
            else:
                uname = st.session_state.iam_user_selected
                user = next((u for u in users if u["UserName"] == uname), None)
                if not user:
                    st.session_state.iam_user_selected = None
                    st.rerun()

                if st.button("← Back to list"):
                    st.session_state.iam_user_selected = None
                    st.rerun()

                st.markdown(f"### {uname}")
                st.caption(f"ARN: `{user.get('Arn', '—')}`")

                try:
                    groups = iam.list_groups_for_user(UserName=uname).get("Groups", [])
                    with st.expander(f"Groups ({len(groups)})"):
                        if groups:
                            st.dataframe([{"Group": g["GroupName"]} for g in groups],
                                         use_container_width=True, hide_index=True)
                        else:
                            st.info("No groups.")
                except Exception:
                    pass

                try:
                    policies = iam.list_attached_user_policies(UserName=uname).get("AttachedPolicies", [])
                    inline = iam.list_user_policies(UserName=uname).get("PolicyNames", [])
                    with st.expander(f"Attached Policies ({len(policies)})"):
                        if policies:
                            st.dataframe([{"Policy": p["PolicyName"]} for p in policies],
                                         use_container_width=True, hide_index=True)
                        else:
                            st.info("No attached policies.")
                    if inline:
                        with st.expander(f"Inline Policies ({len(inline)})"):
                            st.dataframe([{"Policy": p} for p in inline],
                                         use_container_width=True, hide_index=True)
                except Exception:
                    pass

    with tab2:
        try:
            roles = iam.list_roles().get("Roles", [])
        except Exception as e:
            st.error(str(e))
            roles = []

        if not roles:
            st.info("No roles found.")
        else:
            search = st.text_input("🔍 Filter roles", key="iam_role_search", placeholder="e.g. lambda")
            filtered = [r for r in roles if search.lower() in r["RoleName"].lower()] if search else roles
            st.caption(f"{len(filtered)} role(s)")
            st.dataframe([
                {
                    "Role": r["RoleName"],
                    "Created": str(r.get("CreateDate", "—"))[:10],
                    "ARN": r.get("Arn", "—"),
                }
                for r in filtered
            ], use_container_width=True, hide_index=True)

    with tab3:
        try:
            policies = iam.list_policies(Scope="Local").get("Policies", [])
        except Exception as e:
            st.error(str(e))
            policies = []

        if not policies:
            st.info("No customer-managed policies found.")
        else:
            st.caption(f"{len(policies)} policy(s)")
            st.dataframe([
                {
                    "Policy": p["PolicyName"],
                    "Attachments": p.get("AttachmentCount", 0),
                    "Created": str(p.get("CreateDate", "—"))[:10],
                    "ARN": p.get("Arn", "—"),
                }
                for p in policies
            ], use_container_width=True, hide_index=True)
