from datetime import datetime, timezone
import streamlit as st
from aws_client import client


def _fmt_ts(ms: int) -> str:
    if not ms:
        return "—"
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def render():
    st.subheader("📋 CloudWatch Logs")
    logs = client("logs")

    try:
        groups = logs.describe_log_groups().get("logGroups", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not groups:
        st.info("No log groups found.")
        return

    group_names = [g["logGroupName"] for g in groups]

    if "logs_selected" not in st.session_state:
        st.session_state.logs_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.logs_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(group_names)} log group(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for name in group_names:
            c1, c2 = st.columns([8, 1])
            c1.markdown(f"**{name}**")
            if c2.button("View →", key=f"logs_btn_{name}"):
                st.session_state.logs_selected = name
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    selected_group = st.session_state.logs_selected

    if st.button("← Back to list"):
        st.session_state.logs_selected = None
        st.rerun()

    st.markdown(f"### {selected_group}")

    group_detail = next((g for g in groups if g["logGroupName"] == selected_group), {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Stored Bytes", f"{group_detail.get('storedBytes', 0):,}")
    retention = group_detail.get("retentionInDays")
    c2.metric("Retention", f"{retention} days" if retention else "Never expire")
    c3.metric("Creation", _fmt_ts(group_detail.get("creationTime", 0))[:10] if group_detail.get("creationTime") else "—")

    st.divider()

    try:
        streams_resp = logs.describe_log_streams(
            logGroupName=selected_group,
            orderBy="LastEventTime",
            descending=True,
            limit=20,
        )
        stream_list = [s["logStreamName"] for s in streams_resp.get("logStreams", [])]
    except Exception:
        stream_list = []

    col_a, col_b = st.columns([2, 1])
    with col_a:
        if stream_list:
            use_dropdown = st.radio("Stream input", ["Pick from list", "Type manually"], horizontal=True)
        else:
            use_dropdown = "Type manually"
    with col_b:
        limit = st.number_input("Max events", min_value=10, max_value=1000, value=100, step=10)

    if use_dropdown == "Pick from list" and stream_list:
        stream = st.selectbox("Log Stream", stream_list)
    else:
        stream = st.text_input("Log Stream name", placeholder="e.g. my-stream or 2024/01/01/[$LATEST]abc123")

    if not stream:
        st.info("Select or enter a log stream name to view events.")
        return

    with st.expander("Filters"):
        filter_pattern = st.text_input("Filter pattern", placeholder="e.g. ERROR or ?exception ?error", key="log_filter")
        col_f1, _ = st.columns(2)
        start_from_head = col_f1.checkbox("Start from head", value=True)

    try:
        kwargs = dict(
            logGroupName=selected_group,
            logStreamName=stream,
            startFromHead=start_from_head,
            limit=int(limit),
        )
        events = logs.get_log_events(**kwargs).get("events", [])
    except Exception as e:
        st.error(str(e))
        return

    if not events:
        st.info("No events found in this stream.")
        return

    if filter_pattern:
        terms = [t.lstrip("?").lower() for t in filter_pattern.split()]
        events = [e for e in events if any(t in e.get("message", "").lower() for t in terms)]

    st.caption(f"{len(events)} event(s) displayed")
    view = st.radio("Display", ["Log view", "Table"], horizontal=True)

    if view == "Log view":
        lines = []
        for e in events:
            ts = _fmt_ts(e.get("timestamp", 0))
            msg = e.get("message", "").rstrip("\n")
            lines.append(f"{ts}  {msg}")
        st.code("\n".join(lines), language="text")
    else:
        st.dataframe(
            [{"Timestamp": _fmt_ts(e.get("timestamp", 0)), "Message": e.get("message", "").strip()} for e in events],
            use_container_width=True,
            hide_index=True,
        )
