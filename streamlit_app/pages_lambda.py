import json
import base64
import streamlit as st
from aws_client import client


def render():
    st.subheader("Lambda")
    lam = client("lambda")

    try:
        fns = lam.list_functions().get("Functions", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not fns:
        st.info("No functions found.")
        return

    fn_map = {f["FunctionName"]: f for f in fns}
    selected = st.selectbox("Function", list(fn_map.keys()))
    fn = fn_map[selected]

    st.dataframe(
        [{"Field": k, "Value": str(fn.get(k, ""))}
         for k in ("Runtime", "Handler", "MemorySize", "Timeout", "LastModified")],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()
    st.markdown("**Invoke**")
    payload = st.text_area("Payload (JSON)", value="{}", key="lambda_payload")

    if st.button("Invoke"):
        try:
            resp = lam.invoke(FunctionName=selected, Payload=payload.encode())
            status = resp.get("StatusCode")
            func_error = resp.get("FunctionError")
            raw = resp["Payload"].read()
            try:
                body = json.dumps(json.loads(raw), indent=2)
            except Exception:
                body = raw.decode()

            if func_error:
                st.error(f"Status {status} — {func_error}")
            else:
                st.success(f"Status {status}")
            st.code(body, language="json")
        except Exception as e:
            st.error(str(e))

