import json
import streamlit as st
from aws_client import client


def render():
    st.subheader("🔑 Secrets Manager")
    sm = client("secretsmanager")

    if "sm_selected" not in st.session_state:
        st.session_state.sm_selected = None

    try:
        secrets = sm.list_secrets().get("SecretList", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.sm_selected is None:
        col1, col2, col3 = st.columns([5, 1, 1])
        col1.caption(f"{len(secrets)} secret(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        with col3.popover("➕ Create"):
            with st.form("sm_create_form"):
                new_name = st.text_input("Secret Name")
                new_value = st.text_area("Secret Value (string or JSON)", height=80)
                new_desc = st.text_input("Description (optional)")
                if st.form_submit_button("Create Secret"):
                    if not new_name or not new_value:
                        st.warning("Name and value are required.")
                    else:
                        try:
                            sm.create_secret(
                                Name=new_name,
                                SecretString=new_value,
                                Description=new_desc,
                            )
                            st.success(f"Created: {new_name}")
                            st.rerun()
                        except Exception as e:
                            st.error(str(e))

        if not secrets:
            st.info("No secrets found.")
            return

        for s in secrets:
            name = s["Name"]
            last_changed = str(s.get("LastChangedDate", "—"))[:10]
            rotation = "🔄" if s.get("RotationEnabled") else "—"
            c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
            c1.markdown(f"**{name}**")
            c2.caption(f"Changed: {last_changed}")
            c3.caption(rotation)
            if c4.button("View →", key=f"sm_btn_{name}"):
                st.session_state.sm_selected = name
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    selected = st.session_state.sm_selected
    secret = next((s for s in secrets if s["Name"] == selected), None)

    if not secret:
        st.session_state.sm_selected = None
        st.rerun()

    col_back, col_del = st.columns([8, 1])
    if col_back.button("← Back to list"):
        st.session_state.sm_selected = None
        st.rerun()
    with col_del.popover("🗑️ Delete"):
        st.warning(f"Permanently delete **{selected}**? This cannot be undone.")
        if st.button("Confirm delete", type="primary", key="sm_confirm_del"):
            try:
                sm.delete_secret(SecretId=selected, ForceDeleteWithoutRecovery=True)
                st.success(f"Deleted: {selected}")
                st.session_state.sm_selected = None
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.markdown(f"### {selected}")
    if secret.get("Description"):
        st.caption(secret["Description"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Rotation", "Enabled" if secret.get("RotationEnabled") else "Disabled")
    c2.metric("Last Changed", str(secret.get("LastChangedDate", "—"))[:10])
    c3.metric("Last Accessed", str(secret.get("LastAccessedDate", "—"))[:10])

    st.caption(f"ARN: `{secret.get('ARN', '—')}`")

    tab1, tab2, tab3 = st.tabs(["Value", "Versions", "Update"])

    with tab1:
        try:
            val = sm.get_secret_value(SecretId=selected)
            secret_string = val.get("SecretString", "")
            try:
                parsed = json.loads(secret_string)
                st.json(parsed)
            except (json.JSONDecodeError, TypeError):
                st.code(secret_string or "(binary secret)", language="text")
        except Exception as e:
            st.error(f"Cannot retrieve value: {e}")

    with tab2:
        try:
            versions = sm.list_secret_version_ids(SecretId=selected).get("Versions", [])
            if versions:
                rows = [
                    {
                        "Version ID": v.get("VersionId", "—")[:8] + "…",
                        "Stages": ", ".join(v.get("VersionStages", [])),
                        "Created": str(v.get("CreatedDate", "—"))[:19],
                        "Last Accessed": str(v.get("LastAccessedDate", "—"))[:10],
                    }
                    for v in versions
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No versions found.")
        except Exception as e:
            st.error(str(e))

    with tab3:
        with st.form("sm_update_form"):
            new_val = st.text_area("New Secret Value", height=100)
            if st.form_submit_button("Update Value"):
                if not new_val:
                    st.warning("Value cannot be empty.")
                else:
                    try:
                        sm.put_secret_value(SecretId=selected, SecretString=new_val)
                        st.success("Secret value updated.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
