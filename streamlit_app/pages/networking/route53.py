import streamlit as st
from aws_client import client


RECORD_ICONS = {
    "A": "🔵", "AAAA": "🟣", "CNAME": "🟡", "MX": "📧",
    "TXT": "📝", "NS": "🌐", "SOA": "📋", "SRV": "⚙️",
    "PTR": "↩️", "CAA": "🔒", "ALIAS": "🔗",
}


def render():
    st.subheader("🌐 Route 53 — DNS")
    r53 = client("route53")

    if "r53_selected" not in st.session_state:
        st.session_state.r53_selected = None

    try:
        zones = r53.list_hosted_zones().get("HostedZones", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.r53_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(zones)} hosted zone(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not zones:
            st.info("No hosted zones found.")
            return

        for zone in zones:
            zid = zone["Id"].split("/")[-1]
            name = zone.get("Name", "—")
            count = zone.get("ResourceRecordSetCount", "—")
            private = "🔒 Private" if zone.get("Config", {}).get("PrivateZone") else "🌐 Public"

            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.markdown(f"**{name}**")
            c2.caption(private)
            c3.caption(f"{count} records")
            if c4.button("View →", key=f"r53_btn_{zid}"):
                st.session_state.r53_selected = zid
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    zid = st.session_state.r53_selected
    zone = next((z for z in zones if z["Id"].split("/")[-1] == zid), None)
    if not zone:
        st.session_state.r53_selected = None
        st.rerun()

    if st.button("← Back to list"):
        st.session_state.r53_selected = None
        st.rerun()

    name = zone.get("Name", "—")
    private = zone.get("Config", {}).get("PrivateZone", False)
    st.markdown(f"### {name}")
    st.caption(f"Zone ID: `{zid}`")

    c1, c2, c3 = st.columns(3)
    c1.metric("Type", "Private" if private else "Public")
    c2.metric("Record Count", zone.get("ResourceRecordSetCount", "—"))
    c3.metric("Comment", zone.get("Config", {}).get("Comment") or "—")

    st.divider()
    st.markdown("#### Record Sets")

    search = st.text_input("🔍 Filter by name or type", key="r53_search", placeholder="e.g. api or CNAME")

    try:
        records = r53.list_resource_record_sets(HostedZoneId=zid).get("ResourceRecordSets", [])
    except Exception as e:
        st.error(str(e))
        return

    if search:
        records = [
            r for r in records
            if search.lower() in r.get("Name", "").lower()
            or search.upper() in r.get("Type", "")
        ]

    if not records:
        st.info("No records found.")
        return

    for rec in records:
        rtype = rec.get("Type", "—")
        icon = RECORD_ICONS.get(rtype, "⚪")
        rname = rec.get("Name", "—")
        ttl = rec.get("TTL", "—")

        values = []
        if rec.get("AliasTarget"):
            values = [f"ALIAS → {rec['AliasTarget'].get('DNSName', '—')}"]
        else:
            values = [rv.get("Value", "—") for rv in rec.get("ResourceRecords", [])]

        with st.expander(f"{icon} **{rtype}** — {rname}  (TTL: {ttl})"):
            if values:
                st.dataframe(
                    [{"Value": v} for v in values],
                    use_container_width=True,
                    hide_index=True,
                )
