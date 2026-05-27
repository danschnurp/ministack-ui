import streamlit as st
from aws_client import client


def render():
    st.subheader("🏛️ Organizations — AWS Accounts & OUs")
    orgs = client("organizations")

    tab1, tab2, tab3 = st.tabs(["Organization", "Accounts", "Organizational Units"])

    with tab1:
        try:
            org = orgs.describe_organization()["Organization"]
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            return

        st.markdown("#### Organization Overview")
        c1, c2, c3 = st.columns(3)
        c1.metric("Master Account", org.get("MasterAccountId", "—"))
        c2.metric("Feature Set", org.get("FeatureSet", "—"))
        c3.metric("ARN", org.get("Arn", "—")[-20:] + "…")

        st.dataframe([
            {"Field": "Organization ID", "Value": org.get("Id", "—")},
            {"Field": "Master Account ARN", "Value": org.get("MasterAccountArn", "—")},
            {"Field": "Master Account Email", "Value": org.get("MasterAccountEmail", "—")},
        ], use_container_width=True, hide_index=True)

        available_policies = org.get("AvailablePolicyTypes", [])
        if available_policies:
            with st.expander("Available Policy Types"):
                st.dataframe(
                    [{"Type": p.get("Type", "—"), "Status": p.get("Status", "—")} for p in available_policies],
                    use_container_width=True,
                    hide_index=True,
                )

    with tab2:
        try:
            paginator = orgs.get_paginator("list_accounts")
            accounts = [a for page in paginator.paginate() for a in page.get("Accounts", [])]
        except Exception as e:
            st.error(str(e))
            accounts = []

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(accounts)} account(s)")
        if col2.button("🔄 Refresh", key="orgs_acct_refresh", use_container_width=True):
            st.rerun()

        if not accounts:
            st.info("No accounts found.")
        else:
            search = st.text_input("🔍 Filter accounts", placeholder="e.g. dev or account ID")
            filtered = [
                a for a in accounts
                if not search or search.lower() in a.get("Name", "").lower() or search in a.get("Id", "")
            ]
            rows = [
                {
                    "Account ID": a.get("Id", "—"),
                    "Name": a.get("Name", "—"),
                    "Email": a.get("Email", "—"),
                    "Status": a.get("Status", "—"),
                    "Joined": str(a.get("JoinedTimestamp", "—"))[:10],
                    "Joined Method": a.get("JoinedMethod", "—"),
                }
                for a in filtered
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

    with tab3:
        try:
            roots = orgs.list_roots().get("Roots", [])
        except Exception as e:
            st.error(str(e))
            roots = []

        if not roots:
            st.info("No root found.")
            return

        root = roots[0]
        root_id = root["Id"]
        st.caption(f"Root ID: `{root_id}` — {root.get('Name', '—')}")

        def render_ous(parent_id: str, indent: int = 0):
            try:
                ous = orgs.list_organizational_units_for_parent(ParentId=parent_id).get("OrganizationalUnits", [])
                for ou in ous:
                    ou_id = ou["Id"]
                    prefix = "  " * indent + ("└─ " if indent > 0 else "")
                    c1, c2 = st.columns([6, 4])
                    c1.markdown(f"{prefix}**{ou.get('Name', '—')}**")
                    c2.caption(f"ID: `{ou_id}`")
                    render_ous(ou_id, indent + 1)
            except Exception:
                pass

        render_ous(root_id)
