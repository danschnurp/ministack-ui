import streamlit as st
from aws_client import client

METHOD_COLORS = {
    "GET": "🟢", "POST": "🔵", "PUT": "🟡",
    "DELETE": "🔴", "PATCH": "🟣", "OPTIONS": "⚫", "ANY": "⚪",
}


def render():
    st.subheader("🔌 API Gateway")
    apigw = client("apigateway")

    try:
        apis = apigw.get_rest_apis().get("items", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not apis:
        st.info("No REST APIs found.")
        return

    api_map = {f"{a['name']} ({a['id']})": a for a in apis}

    if "apigw_selected" not in st.session_state:
        st.session_state.apigw_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.apigw_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(api_map)} API(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for label, api in api_map.items():
            c1, c2, c3 = st.columns([5, 2, 1])
            c1.markdown(f"**{api['name']}**")
            c2.caption(api.get("endpointConfiguration", {}).get("types", ["—"])[0])
            if c3.button("View →", key=f"apigw_btn_{api['id']}"):
                st.session_state.apigw_selected = label
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    selected_label = st.session_state.apigw_selected
    selected_api = api_map.get(selected_label)
    if not selected_api:
        st.session_state.apigw_selected = None
        st.rerun()

    if st.button("← Back to list"):
        st.session_state.apigw_selected = None
        st.rerun()

    selected_id = selected_api["id"]
    st.markdown(f"### {selected_api['name']}")

    c1, c2, c3 = st.columns(3)
    c1.metric("API ID", selected_id)
    c2.metric("Created", str(selected_api.get("createdDate", "—"))[:10])
    c3.metric("Endpoint Type", selected_api.get("endpointConfiguration", {}).get("types", ["—"])[0])

    if selected_api.get("description"):
        st.caption(selected_api["description"])

    try:
        resources = apigw.get_resources(restApiId=selected_id).get("items", [])
        stages = apigw.get_stages(restApiId=selected_id).get("item", [])
    except Exception as e:
        st.error(str(e))
        return

    tab1, tab2 = st.tabs([f"Resources ({len(resources)})", f"Stages ({len(stages)})"])

    with tab1:
        rows = []
        for r in sorted(resources, key=lambda x: x.get("path", "")):
            methods = list(r.get("resourceMethods", {}).keys())
            method_str = "  ".join(METHOD_COLORS.get(m, "⚪") + " " + m for m in methods) if methods else "—"
            rows.append({"Path": r.get("path", "—"), "Methods": method_str, "Resource ID": r.get("id", "—")})

        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
            resource_paths = [r["Path"] for r in rows]
            selected_path = st.selectbox("Inspect resource", resource_paths, key="apigw_resource")
            res_detail = next((r for r in resources if r.get("path") == selected_path), None)
            if res_detail and res_detail.get("resourceMethods"):
                for method, detail in res_detail["resourceMethods"].items():
                    with st.expander(f"{METHOD_COLORS.get(method, '⚪')} {method}"):
                        try:
                            m_detail = apigw.get_method(restApiId=selected_id, resourceId=res_detail["id"], httpMethod=method)
                            st.json({
                                "authorizationType": m_detail.get("authorizationType"),
                                "apiKeyRequired": m_detail.get("apiKeyRequired"),
                                "requestParameters": m_detail.get("requestParameters", {}),
                            })
                        except Exception:
                            st.json(detail or {})
        else:
            st.info("No resources found.")

    with tab2:
        if stages:
            stage_rows = [
                {
                    "Stage": s.get("stageName", "—"),
                    "Last Deployed": str(s.get("lastUpdatedDate", "—"))[:19],
                    "Cache Enabled": "Yes" if s.get("cacheClusterEnabled") else "No",
                    "Description": s.get("description") or "—",
                }
                for s in stages
            ]
            st.dataframe(stage_rows, use_container_width=True, hide_index=True)
            selected_stage = st.selectbox("Stage", [s.get("stageName") for s in stages], key="apigw_stage")
            region = "us-east-1"
            invoke_url = f"https://{selected_id}.execute-api.{region}.amazonaws.com/{selected_stage}"
            st.markdown("**Invoke URL**")
            st.code(invoke_url, language="text")
        else:
            st.info("No stages deployed.")
