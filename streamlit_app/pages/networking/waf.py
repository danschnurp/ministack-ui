import streamlit as st
from aws_client import client


def render():
    st.subheader("🛡️ WAF")
    waf = client("wafv2")

    scope = st.radio("Scope", ["REGIONAL", "CLOUDFRONT"], horizontal=True)

    tab1, tab2 = st.tabs(["Web ACLs", "IP Sets"])

    with tab1:
        try:
            acls = waf.list_web_acls(Scope=scope).get("WebACLs", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            acls = []

        if not acls:
            st.info(f"No Web ACLs found ({scope}).")
        else:
            if "waf_acl_selected" not in st.session_state:
                st.session_state.waf_acl_selected = None

            if st.session_state.waf_acl_selected is None:
                col1, col2 = st.columns([6, 1])
                col1.caption(f"{len(acls)} Web ACL(s)")
                if col2.button("🔄 Refresh", use_container_width=True, key="waf_refresh"):
                    st.rerun()

                for acl in acls:
                    name = acl["Name"]
                    c1, c2, c3 = st.columns([5, 3, 1])
                    c1.markdown(f"**{name}**")
                    c2.caption(f"`{acl.get('Id', '—')[:12]}…`")
                    if c3.button("View →", key=f"waf_acl_{name}"):
                        st.session_state.waf_acl_selected = (name, acl["Id"], acl.get("LockToken", ""))
                        st.rerun()
            else:
                name, wid, lock = st.session_state.waf_acl_selected

                if st.button("← Back to list"):
                    st.session_state.waf_acl_selected = None
                    st.rerun()

                st.markdown(f"### {name}")

                try:
                    desc = waf.get_web_acl(Name=name, Scope=scope, Id=wid)["WebACL"]
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Default Action", list(desc.get("DefaultAction", {}).keys() or ["—"])[0])
                    c2.metric("Rules", len(desc.get("Rules", [])))
                    c3.metric("Managed Rules", sum(1 for r in desc.get("Rules", []) if r.get("Statement", {}).get("ManagedRuleGroupStatement")))

                    with st.expander("ARN"):
                        st.code(desc.get("ARN", ""), language="text")

                    rules = desc.get("Rules", [])
                    if rules:
                        with st.expander(f"Rules ({len(rules)})"):
                            st.dataframe([
                                {
                                    "Rule": r["Name"],
                                    "Priority": r.get("Priority", "—"),
                                    "Action": list(r.get("Action", r.get("OverrideAction", {"—": None})).keys())[0],
                                }
                                for r in rules
                            ], use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(str(e))

    with tab2:
        try:
            ip_sets = waf.list_ip_sets(Scope=scope).get("IPSets", [])
        except Exception as e:
            st.error(str(e))
            ip_sets = []

        if not ip_sets:
            st.info(f"No IP Sets found ({scope}).")
        else:
            st.caption(f"{len(ip_sets)} IP set(s)")
            selected_ipset = st.selectbox("IP Set", [s["Name"] for s in ip_sets])
            if selected_ipset:
                ipset = next(s for s in ip_sets if s["Name"] == selected_ipset)
                try:
                    detail = waf.get_ip_set(Name=selected_ipset, Scope=scope, Id=ipset["Id"])["IPSet"]
                    addresses = detail.get("Addresses", [])
                    st.caption(f"{len(addresses)} address(es), IP version: {detail.get('IPAddressVersion', '—')}")
                    if addresses:
                        st.dataframe([{"CIDR": a} for a in addresses],
                                     use_container_width=True, hide_index=True)
                    else:
                        st.info("No addresses in this IP set.")
                except Exception as e:
                    st.error(str(e))
