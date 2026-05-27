import streamlit as st
from aws_client import client


def render():
    st.subheader("🌐 API Gateway v2 — HTTP / WebSocket APIs")
    apigw = client("apigatewayv2")

    if "apigwv2_selected" not in st.session_state:
        st.session_state.apigwv2_selected = None

    try:
        apis = apigw.get_apis().get("Items", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.apigwv2_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(apis)} API(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not apis:
            st.info("No HTTP/WebSocket APIs found.")
            return

        for api in apis:
            aid = api["ApiId"]
            protocol = api.get("ProtocolType", "—")
            icon = "🌐" if protocol == "HTTP" else "🔌"
            c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
            c1.markdown(f"**{api.get('Name', '—')}**")
            c2.caption(f"{icon} {protocol}")
            c3.caption(f"`{aid}`")
            if c4.button("View →", key=f"apigwv2_btn_{aid}"):
                st.session_state.apigwv2_selected = aid
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    aid = st.session_state.apigwv2_selected
    api = next((a for a in apis if a["ApiId"] == aid), None)
    if not api:
        st.session_state.apigwv2_selected = None
        st.rerun()

    if st.button("← Back to list"):
        st.session_state.apigwv2_selected = None
        st.rerun()

    protocol = api.get("ProtocolType", "—")
    st.markdown(f"### {api.get('Name', aid)}")
    st.caption(f"ARN: `{api.get('ApiEndpoint', '—')}`")

    c1, c2, c3 = st.columns(3)
    c1.metric("Protocol", protocol)
    c2.metric("API ID", aid)
    c3.metric("Created", str(api.get("CreatedDate", "—"))[:10])

    if api.get("ApiEndpoint"):
        st.code(api["ApiEndpoint"], language="text")

    tab1, tab2, tab3, tab4 = st.tabs(["Routes", "Integrations", "Stages", "Authorizers"])

    with tab1:
        try:
            routes = apigw.get_routes(ApiId=aid).get("Items", [])
            if routes:
                rows = [
                    {
                        "Route Key": r.get("RouteKey", "—"),
                        "Route ID": r.get("RouteId", "—"),
                        "Target": r.get("Target", "—"),
                        "Auth Type": r.get("AuthorizationType", "NONE"),
                    }
                    for r in routes
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No routes defined.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        try:
            integrations = apigw.get_integrations(ApiId=aid).get("Items", [])
            if integrations:
                rows = [
                    {
                        "Integration ID": i.get("IntegrationId", "—"),
                        "Type": i.get("IntegrationType", "—"),
                        "Method": i.get("IntegrationMethod", "—"),
                        "URI": (i.get("IntegrationUri") or "—")[:60],
                    }
                    for i in integrations
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No integrations found.")
        except Exception as e:
            st.error(str(e))

    with tab3:
        try:
            stages = apigw.get_stages(ApiId=aid).get("Items", [])
            if stages:
                rows = [
                    {
                        "Stage": s.get("StageName", "—"),
                        "Auto Deploy": "Yes" if s.get("AutoDeploy") else "No",
                        "Deployment ID": s.get("DeploymentId", "—"),
                        "Last Updated": str(s.get("LastUpdatedDate", "—"))[:19],
                    }
                    for s in stages
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No stages found.")
        except Exception as e:
            st.error(str(e))

    with tab4:
        try:
            authorizers = apigw.get_authorizers(ApiId=aid).get("Items", [])
            if authorizers:
                rows = [
                    {
                        "Name": a.get("Name", "—"),
                        "Type": a.get("AuthorizerType", "—"),
                        "Identity Source": ", ".join(a.get("IdentitySource", [])),
                    }
                    for a in authorizers
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No authorizers found.")
        except Exception as e:
            st.error(str(e))
