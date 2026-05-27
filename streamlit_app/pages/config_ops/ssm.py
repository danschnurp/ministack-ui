import streamlit as st
from aws_client import client


TYPE_ICONS = {"String": "📄", "StringList": "📋", "SecureString": "🔐"}


def render():
    st.subheader("📐 SSM — Parameter Store")
    ssm = client("ssm")

    tab1, tab2 = st.tabs(["Parameters", "Put Parameter"])

    with tab1:
        path = st.text_input("Path prefix", value="/", placeholder="/myapp/")
        recursive = st.checkbox("Recursive", value=True)
        col1, col2 = st.columns([6, 1])

        try:
            kwargs = dict(Path=path, Recursive=recursive, WithDecryption=True)
            paginator = ssm.get_paginator("get_parameters_by_path")
            pages = paginator.paginate(**kwargs)
            params = [p for page in pages for p in page.get("Parameters", [])]
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            params = []

        col1.caption(f"{len(params)} parameter(s) under `{path}`")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not params:
            st.info("No parameters found.")
        else:
            search = st.text_input("🔍 Filter by name", placeholder="e.g. database")
            if search:
                params = [p for p in params if search.lower() in p.get("Name", "").lower()]

            for p in params:
                ptype = p.get("Type", "String")
                icon = TYPE_ICONS.get(ptype, "📄")
                pname = p.get("Name", "—")
                version = p.get("Version", "—")
                value = p.get("Value", "")
                display_val = "••••••••" if ptype == "SecureString" else (value[:60] + "…" if len(value) > 60 else value)

                with st.expander(f"{icon} `{pname}` (v{version})"):
                    c1, c2 = st.columns(2)
                    c1.metric("Type", ptype)
                    c2.metric("Version", version)
                    st.code(value, language="text")
                    st.caption(f"Modified: {str(p.get('LastModifiedDate', '—'))[:19]}")

    with tab2:
        with st.form("ssm_put_form"):
            pname = st.text_input("Parameter Name", placeholder="/myapp/db/password")
            pvalue = st.text_area("Value", height=80)
            ptype = st.selectbox("Type", ["String", "StringList", "SecureString"])
            description = st.text_input("Description (optional)")
            overwrite = st.checkbox("Overwrite if exists", value=True)
            submitted = st.form_submit_button("Put Parameter")

        if submitted:
            if not pname or not pvalue:
                st.warning("Name and value are required.")
            else:
                try:
                    kwargs = dict(
                        Name=pname,
                        Value=pvalue,
                        Type=ptype,
                        Overwrite=overwrite,
                    )
                    if description:
                        kwargs["Description"] = description
                    resp = ssm.put_parameter(**kwargs)
                    st.success(f"Parameter stored at version {resp.get('Version', '—')}.")
                except Exception as e:
                    st.error(f"Failed: {e}")
