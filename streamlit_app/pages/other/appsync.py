import streamlit as st
from aws_client import client


AUTH_ICONS = {
    "API_KEY": "🔑", "AWS_IAM": "🔐", "AMAZON_COGNITO_USER_POOLS": "👤",
    "OPENID_CONNECT": "🌐", "AWS_LAMBDA": "⚡",
}


def render():
    st.subheader("⚡ AppSync — GraphQL APIs")
    appsync = client("appsync")

    if "appsync_selected" not in st.session_state:
        st.session_state.appsync_selected = None

    try:
        apis = appsync.list_graphql_apis().get("graphqlApis", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.appsync_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(apis)} GraphQL API(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not apis:
            st.info("No AppSync APIs found.")
            return

        for api in apis:
            aid = api["apiId"]
            name = api.get("name", "—")
            auth = api.get("authenticationType", "—")
            icon = AUTH_ICONS.get(auth, "⚪")

            c1, c2, c3, c4 = st.columns([4, 3, 2, 1])
            c1.markdown(f"**{name}**")
            c2.caption(f"{icon} {auth}")
            c3.caption(f"ID: `{aid}`")
            if c4.button("View →", key=f"appsync_btn_{aid}"):
                st.session_state.appsync_selected = aid
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    aid = st.session_state.appsync_selected
    api = next((a for a in apis if a["apiId"] == aid), None)
    if not api:
        st.session_state.appsync_selected = None
        st.rerun()

    if st.button("← Back to APIs"):
        st.session_state.appsync_selected = None
        st.rerun()

    name = api.get("name", "—")
    auth = api.get("authenticationType", "—")
    icon = AUTH_ICONS.get(auth, "⚪")
    st.markdown(f"### {name}")
    st.caption(f"ARN: `{api.get('arn', '—')}`")

    uris = api.get("uris", {})
    if uris.get("GRAPHQL"):
        st.code(uris["GRAPHQL"], language="text")

    c1, c2 = st.columns(2)
    c1.metric("Auth Type", f"{icon} {auth}")
    c2.metric("API ID", aid)

    tab1, tab2, tab3, tab4 = st.tabs(["Data Sources", "Resolvers / Functions", "API Keys", "Schema"])

    with tab1:
        try:
            sources = appsync.list_data_sources(apiId=aid).get("dataSources", [])
            if sources:
                rows = [
                    {
                        "Name": ds.get("name", "—"),
                        "Type": ds.get("type", "—"),
                        "Description": ds.get("description", "—")[:50],
                    }
                    for ds in sources
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No data sources found.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        try:
            functions = appsync.list_functions(apiId=aid).get("functions", [])
            if functions:
                rows = [
                    {
                        "Name": f.get("name", "—"),
                        "Data Source": f.get("dataSourceName", "—"),
                        "Function ID": f.get("functionId", "—"),
                        "Runtime": f.get("runtime", {}).get("name", "VTL"),
                    }
                    for f in functions
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No pipeline functions found.")
        except Exception as e:
            st.error(str(e))

    with tab3:
        try:
            keys = appsync.list_api_keys(apiId=aid).get("apiKeys", [])
            if keys:
                rows = [
                    {
                        "Key ID": k.get("id", "—"),
                        "Description": k.get("description", "—"),
                        "Expires": str(k.get("expires", "—")),
                    }
                    for k in keys
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No API keys found.")
        except Exception as e:
            st.error(str(e))

    with tab4:
        try:
            schema = appsync.get_introspection_schema(apiId=aid, format="SDL").get("schema")
            if schema:
                st.code(schema.read().decode() if hasattr(schema, "read") else str(schema), language="graphql")
            else:
                st.info("No schema found.")
        except Exception as e:
            st.info(f"Schema not available: {e}")
