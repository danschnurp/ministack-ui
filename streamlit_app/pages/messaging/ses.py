import streamlit as st
from aws_client import client


VERIFY_ICONS = {"Success": "🟢", "Pending": "🟡", "Failed": "🔴", "TemporaryFailure": "🟠", "NotStarted": "⚫"}


def render():
    st.subheader("✉️ SES — Simple Email Service")
    ses = client("ses")

    tab1, tab2 = st.tabs(["Identities", "Send Email"])

    with tab1:
        try:
            identities = ses.list_identities().get("Identities", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            identities = []

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(identities)} identity(ies)")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not identities:
            st.info("No SES identities found. Add a domain or email address to get started.")
        else:
            try:
                attrs = ses.get_identity_verification_attributes(Identities=identities).get("VerificationAttributes", {})
            except Exception:
                attrs = {}

            try:
                dkim_attrs = ses.get_identity_dkim_attributes(Identities=identities).get("DkimAttributes", {})
            except Exception:
                dkim_attrs = {}

            for identity in identities:
                attr = attrs.get(identity, {})
                status = attr.get("VerificationStatus", "—")
                icon = VERIFY_ICONS.get(status, "⚪")
                dkim = dkim_attrs.get(identity, {})
                dkim_enabled = "✅" if dkim.get("DkimEnabled") else "❌"
                dkim_verified = dkim.get("DkimVerificationStatus", "—")

                with st.expander(f"{icon} **{identity}** — {status}"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Verification", status)
                    c2.metric("DKIM Enabled", dkim_enabled)
                    c3.metric("DKIM Verified", dkim_verified)

                    token = attr.get("VerificationToken")
                    if token:
                        st.code(f"TXT verification token: {token}", language="text")

                    dkim_tokens = dkim.get("DkimTokens", [])
                    if dkim_tokens:
                        st.markdown("**DKIM CNAME Records (add to DNS)**")
                        domain = identity if "." in identity else identity.split("@")[-1]
                        for t in dkim_tokens:
                            st.code(f"{t}._domainkey.{domain}. CNAME {t}.dkim.amazonses.com.", language="text")

    with tab2:
        st.markdown("#### Send a Test Email")
        with st.form("ses_send_form"):
            from_addr = st.text_input("From (verified identity)", placeholder="sender@example.com")
            to_addr = st.text_input("To", placeholder="recipient@example.com")
            subject = st.text_input("Subject", value="Test from MiniStack")
            body = st.text_area("Body (plain text)", value="Hello from MiniStack SES!", height=100)
            submitted = st.form_submit_button("Send Email")

        if submitted:
            if not from_addr or not to_addr:
                st.warning("From and To addresses are required.")
            else:
                try:
                    resp = ses.send_email(
                        Source=from_addr,
                        Destination={"ToAddresses": [to_addr]},
                        Message={
                            "Subject": {"Data": subject},
                            "Body": {"Text": {"Data": body}},
                        },
                    )
                    st.success(f"Email sent! Message ID: `{resp.get('MessageId', '—')}`")
                except Exception as e:
                    st.error(f"Failed: {e}")
