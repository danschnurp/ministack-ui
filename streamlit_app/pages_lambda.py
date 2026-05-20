import json
import streamlit as st
from aws_client import client

RUNTIME_ICONS = {
    "python": "🐍", "nodejs": "🟩", "java": "☕",
    "go": "🐹", "ruby": "💎", "dotnet": "🔷",
}


def _runtime_icon(runtime: str) -> str:
    r = (runtime or "").lower()
    for k, v in RUNTIME_ICONS.items():
        if k in r:
            return f"{v} {runtime}"
    return runtime


def render():
    st.subheader("⚡ Lambda")
    lam = client("lambda")

    # ── fetch list ────────────────────────────────────────────────────────────
    try:
        fns = lam.list_functions().get("Functions", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not fns:
        st.info("No functions found.")
        return

    fn_map = {f["FunctionName"]: f for f in fns}

    # ── drill-down state ──────────────────────────────────────────────────────
    if "lambda_selected" not in st.session_state:
        st.session_state.lambda_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.lambda_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(fns)} function(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for name, fn in fn_map.items():
            with st.container():
                c1, c2, c3, c4 = st.columns([4, 2, 1, 1])
                c1.markdown(f"**{name}**")
                c2.caption(_runtime_icon(fn.get("Runtime", "—")))
                c3.caption(f"{fn.get('MemorySize', '—')} MB")
                if c4.button("View →", key=f"lambda_btn_{name}"):
                    st.session_state.lambda_selected = name
                    st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    selected = st.session_state.lambda_selected
    if selected not in fn_map:
        st.session_state.lambda_selected = None
        st.rerun()

    fn = fn_map[selected]

    if st.button("← Back to list"):
        st.session_state.lambda_selected = None
        st.rerun()

    st.markdown(f"### {selected}")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Runtime", _runtime_icon(fn.get("Runtime", "—")))
    c2.metric("Memory", f"{fn.get('MemorySize', '—')} MB")
    c3.metric("Timeout", f"{fn.get('Timeout', '—')}s")
    c4.metric("Code Size", f"{fn.get('CodeSize', 0) // 1024} KB")

    details = [
        {"Field": "Handler", "Value": fn.get("Handler", "—")},
        {"Field": "Role", "Value": fn.get("Role", "—")},
        {"Field": "Description", "Value": fn.get("Description") or "—"},
        {"Field": "Last Modified", "Value": str(fn.get("LastModified", "—"))[:19]},
        {"Field": "Function ARN", "Value": fn.get("FunctionArn", "—")},
    ]
    with st.expander("Function Details"):
        st.dataframe(details, use_container_width=True, hide_index=True)

    env_vars = fn.get("Environment", {}).get("Variables", {})
    if env_vars:
        with st.expander(f"Environment Variables ({len(env_vars)})"):
            st.dataframe(
                [{"Key": k, "Value": "●●●●●●" if any(s in k.upper() for s in ("SECRET", "KEY", "TOKEN", "PASS", "PWD")) else v}
                 for k, v in env_vars.items()],
                use_container_width=True,
                hide_index=True,
            )

    st.divider()
    st.markdown("**Invoke**")

    payload_presets = {"Empty `{}`": "{}", "Custom": None}
    preset = st.radio("Payload preset", list(payload_presets.keys()), horizontal=True)
    default_payload = payload_presets[preset] or "{}"

    payload = st.text_area("Payload (JSON)", value=default_payload, key="lambda_payload", height=120)

    payload_valid = True
    try:
        json.loads(payload)
    except json.JSONDecodeError as e:
        st.warning(f"⚠️ Invalid JSON: {e}")
        payload_valid = False

    invoke_type = st.radio("Invocation type", ["RequestResponse", "Event (async)", "DryRun"], horizontal=True)
    type_map = {"RequestResponse": "RequestResponse", "Event (async)": "Event", "DryRun": "DryRun"}

    if st.button("▶ Invoke", disabled=not payload_valid):
        try:
            resp = lam.invoke(
                FunctionName=selected,
                InvocationType=type_map[invoke_type],
                Payload=payload.encode(),
            )
            status = resp.get("StatusCode")
            func_error = resp.get("FunctionError")
            raw = resp["Payload"].read()

            if type_map[invoke_type] == "Event":
                st.success(f"Status {status} — async invocation accepted")
            elif type_map[invoke_type] == "DryRun":
                st.success(f"Status {status} — dry run succeeded (function not executed)")
            else:
                try:
                    body = json.dumps(json.loads(raw), indent=2)
                except Exception:
                    body = raw.decode()
                if func_error:
                    st.error(f"Status {status} — {func_error}")
                else:
                    st.success(f"Status {status} — OK")
                st.code(body, language="json")
        except Exception as e:
            st.error(str(e))
