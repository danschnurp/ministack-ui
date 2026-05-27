import streamlit as st
from aws_client import client


STATUS_ICONS = {
    "ISSUED": "🟢",
    "PENDING_VALIDATION": "🟡",
    "EXPIRED": "🔴",
    "INACTIVE": "⚫",
    "FAILED": "🔴",
    "REVOKED": "🔴",
    "VALIDATION_TIMED_OUT": "🔴",
}


def render():
    st.subheader("🔒 ACM — Certificate Manager")
    acm = client("acm")

    if "acm_selected" not in st.session_state:
        st.session_state.acm_selected = None

    try:
        certs_list = acm.list_certificates().get("CertificateSummaryList", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.acm_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(certs_list)} certificate(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not certs_list:
            st.info("No certificates found.")
            return

        for cert in certs_list:
            arn = cert["CertificateArn"]
            domain = cert.get("DomainName", "—")
            status = cert.get("Status", "—")
            icon = STATUS_ICONS.get(status, "⚪")
            short_arn = arn.split("/")[-1][:12] + "…"

            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.markdown(f"**{domain}**")
            c2.caption(f"{icon} {status}")
            c3.caption(f"`{short_arn}`")
            if c4.button("View →", key=f"acm_btn_{arn}"):
                st.session_state.acm_selected = arn
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    arn = st.session_state.acm_selected

    if st.button("← Back to list"):
        st.session_state.acm_selected = None
        st.rerun()

    try:
        cert = acm.describe_certificate(CertificateArn=arn)["Certificate"]
    except Exception as e:
        st.error(str(e))
        return

    status = cert.get("Status", "—")
    icon = STATUS_ICONS.get(status, "⚪")
    st.markdown(f"### {cert.get('DomainName', '—')}")
    st.caption(f"ARN: `{arn}`")

    c1, c2, c3 = st.columns(3)
    c1.metric("Status", f"{icon} {status}")
    c2.metric("Type", cert.get("Type", "—"))
    c3.metric("Key Algorithm", cert.get("KeyAlgorithm", "—"))

    c4, c5, c6 = st.columns(3)
    c4.metric("Issued", str(cert.get("IssuedAt", "—"))[:10])
    c5.metric("Expires", str(cert.get("NotAfter", "—"))[:10])
    c6.metric("Renewal Eligibility", cert.get("RenewalEligibility", "—"))

    tab1, tab2, tab3 = st.tabs(["SANs", "Validation", "Details"])

    with tab1:
        sans = cert.get("SubjectAlternativeNames", [])
        if sans:
            st.dataframe([{"Domain": d} for d in sans], use_container_width=True, hide_index=True)
        else:
            st.info("No SANs.")

    with tab2:
        options = cert.get("DomainValidationOptions", [])
        if options:
            rows = []
            for opt in options:
                rec = opt.get("ResourceRecord", {})
                rows.append({
                    "Domain": opt.get("DomainName", "—"),
                    "Validation Status": opt.get("ValidationStatus", "—"),
                    "Validation Method": opt.get("ValidationMethod", "—"),
                    "DNS Record Name": rec.get("Name", "—"),
                    "DNS Record Value": rec.get("Value", "—"),
                    "DNS Record Type": rec.get("Type", "—"),
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No validation options found.")

    with tab3:
        fields = [
            ("Issuer", cert.get("Issuer", "—")),
            ("Subject", cert.get("Subject", "—")),
            ("Serial", cert.get("Serial", "—")),
            ("Signature Algorithm", cert.get("SignatureAlgorithm", "—")),
            ("Not Before", str(cert.get("NotBefore", "—"))[:19]),
            ("Not After", str(cert.get("NotAfter", "—"))[:19]),
            ("In Use By", ", ".join(cert.get("InUseBy", [])) or "—"),
        ]
        st.dataframe(
            [{"Field": f, "Value": v} for f, v in fields],
            use_container_width=True,
            hide_index=True,
        )

        tags_resp = None
        try:
            tags_resp = acm.list_tags_for_certificate(CertificateArn=arn).get("Tags", [])
        except Exception:
            pass

        if tags_resp:
            with st.expander(f"Tags ({len(tags_resp)})"):
                st.dataframe(
                    [{"Key": t["Key"], "Value": t.get("Value", "")} for t in tags_resp],
                    use_container_width=True,
                    hide_index=True,
                )
