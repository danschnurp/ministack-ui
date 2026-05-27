import streamlit as st
from aws_client import client


def render():
    st.subheader("📡 IoT Core — Things, Certificates & Policies")
    iot = client("iot")

    tab1, tab2, tab3 = st.tabs(["Things", "Certificates", "Policies"])

    with tab1:
        try:
            things = iot.list_things().get("things", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            things = []

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(things)} thing(s)")
        if col2.button("🔄 Refresh", key="iot_things_refresh", use_container_width=True):
            st.rerun()

        if not things:
            st.info("No IoT Things found.")
        else:
            for t in things:
                tname = t.get("thingName", "—")
                ttype = t.get("thingTypeName", "—") or "—"
                arn = t.get("thingArn", "—")

                with st.expander(f"**{tname}** ({ttype})"):
                    st.caption(f"ARN: `{arn}`")
                    attrs = t.get("attributes", {})
                    if attrs:
                        st.dataframe(
                            [{"Attribute": k, "Value": v} for k, v in attrs.items()],
                            use_container_width=True,
                            hide_index=True,
                        )
                    try:
                        principals = iot.list_thing_principals(thingName=tname).get("principals", [])
                        if principals:
                            st.markdown("**Attached Principals (Certs)**")
                            st.dataframe(
                                [{"Principal": p.split("cert/")[-1][:16] + "…"} for p in principals],
                                use_container_width=True,
                                hide_index=True,
                            )
                    except Exception:
                        pass

    with tab2:
        try:
            certs = iot.list_certificates().get("certificates", [])
        except Exception as e:
            st.error(str(e))
            certs = []

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(certs)} certificate(s)")
        if col2.button("🔄 Refresh", key="iot_certs_refresh", use_container_width=True):
            st.rerun()

        if not certs:
            st.info("No certificates found.")
        else:
            rows = [
                {
                    "Certificate ID": c.get("certificateId", "—")[:16] + "…",
                    "Status": c.get("status", "—"),
                    "Created": str(c.get("creationDate", "—"))[:10],
                }
                for c in certs
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

    with tab3:
        try:
            policies = iot.list_policies().get("policies", [])
        except Exception as e:
            st.error(str(e))
            policies = []

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(policies)} policy(ies)")
        if col2.button("🔄 Refresh", key="iot_policies_refresh", use_container_width=True):
            st.rerun()

        if not policies:
            st.info("No IoT policies found.")
        else:
            for p in policies:
                pname = p.get("policyName", "—")
                arn = p.get("policyArn", "—")
                with st.expander(f"**{pname}**"):
                    st.caption(f"ARN: `{arn}`")
                    try:
                        doc = iot.get_policy(policyName=pname)
                        st.code(doc.get("policyDocument", "{}"), language="json")
                    except Exception as e:
                        st.error(str(e))
