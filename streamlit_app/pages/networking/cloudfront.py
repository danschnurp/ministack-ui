import streamlit as st
from aws_client import client


STATE_ICONS = {
    "Deployed": "🟢",
    "InProgress": "🟡",
    "Disabled": "🔴",
}


def render():
    st.subheader("☁️ CloudFront — Distributions")
    cf = client("cloudfront")

    if "cf_selected" not in st.session_state:
        st.session_state.cf_selected = None

    try:
        resp = cf.list_distributions()
        dist_list = resp.get("DistributionList", {})
        dists = dist_list.get("Items", []) or []
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.cf_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(dists)} distribution(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not dists:
            st.info("No CloudFront distributions found.")
            return

        for dist in dists:
            did = dist["Id"]
            status = dist.get("Status", "—")
            icon = STATE_ICONS.get(status, "⚪")
            domain = dist.get("DomainName", "—")
            enabled = "🟢 Enabled" if dist.get("Enabled") else "🔴 Disabled"
            aliases = dist.get("Aliases", {}).get("Items", [])
            alias_str = aliases[0] if aliases else "—"

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.markdown(f"**{alias_str}**")
            c2.caption(f"{icon} {status}")
            c3.caption(enabled)
            c4.caption(domain[:30])
            if c5.button("View →", key=f"cf_btn_{did}"):
                st.session_state.cf_selected = did
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    did = st.session_state.cf_selected
    dist = next((d for d in dists if d["Id"] == did), None)
    if not dist:
        st.session_state.cf_selected = None
        st.rerun()

    if st.button("← Back to list"):
        st.session_state.cf_selected = None
        st.rerun()

    try:
        detail_resp = cf.get_distribution(Id=did)
        detail = detail_resp["Distribution"]["DistributionConfig"]
        dist_info = detail_resp["Distribution"]
    except Exception as e:
        st.error(str(e))
        return

    status = dist_info.get("Status", "—")
    icon = STATE_ICONS.get(status, "⚪")
    aliases = detail.get("Aliases", {}).get("Items", [])
    title = aliases[0] if aliases else dist_info.get("DomainName", did)

    st.markdown(f"### {title}")
    st.caption(f"Distribution ID: `{did}`  |  Domain: `{dist_info.get('DomainName', '—')}`")

    c1, c2, c3 = st.columns(3)
    c1.metric("Status", f"{icon} {status}")
    c2.metric("Enabled", "Yes" if detail.get("Enabled") else "No")
    c3.metric("Price Class", detail.get("PriceClass", "—"))

    c4, c5 = st.columns(2)
    c4.metric("HTTP Version", detail.get("HttpVersion", "—"))
    c5.metric("IPv6", "Yes" if detail.get("IsIPV6Enabled") else "No")

    tab1, tab2, tab3 = st.tabs(["Origins", "Cache Behaviors", "Details"])

    with tab1:
        origins = detail.get("Origins", {}).get("Items", [])
        if origins:
            rows = [
                {
                    "Origin ID": o.get("Id", "—"),
                    "Domain Name": o.get("DomainName", "—"),
                    "Path": o.get("OriginPath") or "/",
                    "Protocol": o.get("CustomOriginConfig", {}).get("OriginProtocolPolicy", "S3"),
                }
                for o in origins
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No origins configured.")

    with tab2:
        behaviors = detail.get("CacheBehaviors", {}).get("Items", [])
        default_cb = detail.get("DefaultCacheBehavior", {})

        if default_cb:
            st.markdown("**Default Cache Behavior**")
            st.dataframe([
                {"Field": "Target Origin ID", "Value": default_cb.get("TargetOriginId", "—")},
                {"Field": "Viewer Protocol", "Value": default_cb.get("ViewerProtocolPolicy", "—")},
                {"Field": "Compress", "Value": str(default_cb.get("Compress", False))},
                {"Field": "Cache Policy ID", "Value": default_cb.get("CachePolicyId", "—")},
            ], use_container_width=True, hide_index=True)

        if behaviors:
            st.markdown("**Custom Cache Behaviors**")
            rows = [
                {
                    "Path Pattern": b.get("PathPattern", "—"),
                    "Target Origin": b.get("TargetOriginId", "—"),
                    "Viewer Protocol": b.get("ViewerProtocolPolicy", "—"),
                }
                for b in behaviors
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

    with tab3:
        comment = detail.get("Comment") or "—"
        geo = detail.get("Restrictions", {}).get("GeoRestriction", {})
        st.dataframe([
            {"Field": "Comment", "Value": comment},
            {"Field": "Aliases", "Value": ", ".join(aliases) or "—"},
            {"Field": "Geo Restriction", "Value": geo.get("RestrictionType", "none")},
            {"Field": "Web ACL ID", "Value": detail.get("WebACLId") or "—"},
            {"Field": "Last Modified", "Value": str(dist_info.get("LastModifiedTime", "—"))[:19]},
        ], use_container_width=True, hide_index=True)
