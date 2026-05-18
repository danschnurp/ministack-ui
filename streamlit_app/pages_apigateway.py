import streamlit as st
from aws_client import client

METHOD_COLORS = {
    "GET": "🟢", "POST": "🔵", "PUT": "🟡",
    "DELETE": "🔴", "PATCH": "🟣", "ANY": "⚪",
}


def render():
    st.subheader("API Gateway")
    apigw = client("apigateway")

    try:
        apis = apigw.get_rest_apis().get("items", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not apis:
        st.info("No REST APIs found.")
        return

    api_map = {a["name"]: a["id"] for a in apis}
    selected_name = st.selectbox("REST API", list(api_map.keys()))
    selected_id = api_map[selected_name]

    try:
        resources = apigw.get_resources(restApiId=selected_id).get("items", [])
        stages = apigw.get_stages(restApiId=selected_id).get("item", [])
    except Exception as e:
        st.error(str(e))
        return

    st.markdown("**Resources**")
    st.dataframe(
        [{"Path": r.get("path", ""),
          "Methods": " ".join(
              METHOD_COLORS.get(m, "⚪") + " " + m
              for m in r.get("resourceMethods", {}).keys()
          )}
         for r in resources],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("**Stages**")
    st.dataframe(
        [{"Stage": s.get("stageName", ""), "Last deployed": str(s.get("lastUpdatedDate", ""))}
         for s in stages],
        use_container_width=True,
        hide_index=True,
    )

