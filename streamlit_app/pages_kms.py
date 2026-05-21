import streamlit as st
from aws_client import client


def render():
    st.subheader("🔐 KMS")
    kms = client("kms")

    try:
        keys_resp = kms.list_keys()
        key_metas = keys_resp.get("Keys", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not key_metas:
        st.info("No KMS keys found.")
        return

    if "kms_selected" not in st.session_state:
        st.session_state.kms_selected = None

    # Fetch basic metadata for list
    keys = []
    for k in key_metas:
        try:
            meta = kms.describe_key(KeyId=k["KeyId"])["KeyMetadata"]
            keys.append(meta)
        except Exception:
            keys.append({"KeyId": k["KeyId"], "KeyState": "—", "Description": "—"})

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.kms_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(keys)} key(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for key in keys:
            kid = key["KeyId"]
            state = key.get("KeyState", "—")
            icon = "🟢" if state == "Enabled" else "🔴" if state == "Disabled" else "🟡"
            desc = key.get("Description") or "(no description)"
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.markdown(f"`{kid[:8]}…`")
            c2.caption(f"{icon} {state}")
            c3.caption(desc[:30])
            if c4.button("View →", key=f"kms_btn_{kid}"):
                st.session_state.kms_selected = kid
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    kid = st.session_state.kms_selected
    key = next((k for k in keys if k["KeyId"] == kid), None)

    if not key:
        st.session_state.kms_selected = None
        st.rerun()

    if st.button("← Back to list"):
        st.session_state.kms_selected = None
        st.rerun()

    state = key.get("KeyState", "—")
    icon = "🟢" if state == "Enabled" else "🔴"
    st.markdown(f"### {key.get('Description') or kid}")

    c1, c2, c3 = st.columns(3)
    c1.metric("State", f"{icon} {state}")
    c2.metric("Usage", key.get("KeyUsage", "—"))
    c3.metric("Origin", key.get("Origin", "—"))

    with st.expander("Key Details"):
        st.dataframe([
            {"Field": "Key ID", "Value": key.get("KeyId", "—")},
            {"Field": "ARN", "Value": key.get("Arn", "—")},
            {"Field": "Spec", "Value": key.get("KeySpec", "—")},
            {"Field": "Manager", "Value": key.get("KeyManager", "—")},
            {"Field": "Created", "Value": str(key.get("CreationDate", "—"))[:19]},
            {"Field": "Enabled", "Value": str(key.get("Enabled", "—"))},
            {"Field": "Multi-Region", "Value": str(key.get("MultiRegion", False))},
        ], use_container_width=True, hide_index=True)

    try:
        aliases = kms.list_aliases(KeyId=kid).get("Aliases", [])
        if aliases:
            with st.expander(f"Aliases ({len(aliases)})"):
                st.dataframe([{"Alias": a["AliasName"]} for a in aliases],
                             use_container_width=True, hide_index=True)
    except Exception:
        pass

    try:
        policy_names = kms.list_key_policies(KeyId=kid).get("PolicyNames", [])
        if policy_names:
            with st.expander(f"Key Policy"):
                policy = kms.get_key_policy(KeyId=kid, PolicyName=policy_names[0]).get("Policy", "")
                st.code(policy, language="json")
    except Exception:
        pass
