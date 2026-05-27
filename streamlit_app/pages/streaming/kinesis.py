import streamlit as st
from aws_client import client


def render():
    st.subheader("🌊 Kinesis")
    kin = client("kinesis")

    try:
        streams = kin.list_streams()["StreamNames"]
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not streams:
        st.info("No streams found.")
        return

    if "kinesis_selected" not in st.session_state:
        st.session_state.kinesis_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.kinesis_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(streams)} stream(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for name in streams:
            c1, c2 = st.columns([8, 1])
            c1.markdown(f"**{name}**")
            if c2.button("View →", key=f"kinesis_btn_{name}"):
                st.session_state.kinesis_selected = name
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    selected = st.session_state.kinesis_selected

    if st.button("← Back to list"):
        st.session_state.kinesis_selected = None
        st.rerun()

    st.markdown(f"### {selected}")

    try:
        summary = kin.describe_stream_summary(StreamName=selected)["StreamDescriptionSummary"]
        shards = kin.list_shards(StreamName=selected)["Shards"]
    except Exception as e:
        st.error(str(e))
        return

    status = summary.get("StreamStatus", "")
    color = "🟢" if status == "ACTIVE" else "🔴" if status == "DELETING" else "🟡"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", f"{color} {status}")
    c2.metric("Shards", summary.get("OpenShardCount", 0))
    c3.metric("Retention (hrs)", summary.get("RetentionPeriodHours", "—"))
    c4.metric("Encryption", summary.get("EncryptionType", "NONE"))

    st.divider()
    with st.expander("Stream ARN"):
        st.code(summary.get("StreamARN", ""), language="text")

    st.markdown("**Shards**")
    shard_rows = [
        {
            "Shard ID": s["ShardId"],
            "Parent Shard": s.get("ParentShardId", "—"),
            "Starting Hash Key": s["HashKeyRange"]["StartingHashKey"][:20] + "…",
            "Ending Hash Key": s["HashKeyRange"]["EndingHashKey"][:20] + "…",
            "Starting Seq No": s["SequenceNumberRange"].get("StartingSequenceNumber", "—")[:16] + "…",
        }
        for s in shards
    ]
    st.dataframe(shard_rows, use_container_width=True, hide_index=True)
    st.caption(f"{len(shards)} shard(s) total")
