import streamlit as st
from aws_client import client


def render():
    st.subheader("🌊 DynamoDB Streams")
    ddb = client("dynamodb")
    streams_client = client("dynamodbstreams")

    if "ddbstream_selected" not in st.session_state:
        st.session_state.ddbstream_selected = None

    try:
        streams = streams_client.list_streams().get("Streams", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.ddbstream_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(streams)} stream(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not streams:
            st.info("No DynamoDB Streams found. Enable streaming on a DynamoDB table first.")
            return

        for s in streams:
            arn = s["StreamArn"]
            table = s.get("TableName", "—")
            label = s.get("StreamLabel", "—")

            c1, c2, c3, c4 = st.columns([3, 3, 3, 1])
            c1.markdown(f"**{table}**")
            c2.caption(f"Label: {label}")
            c3.caption(arn[-20:] + "…")
            if c4.button("View →", key=f"ddbstream_btn_{arn}"):
                st.session_state.ddbstream_selected = arn
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    arn = st.session_state.ddbstream_selected
    stream = next((s for s in streams if s["StreamArn"] == arn), None)
    if not stream:
        st.session_state.ddbstream_selected = None
        st.rerun()

    if st.button("← Back to streams"):
        st.session_state.ddbstream_selected = None
        st.rerun()

    table = stream.get("TableName", "—")
    st.markdown(f"### Stream: {table}")
    st.caption(f"ARN: `{arn}`")

    try:
        desc = streams_client.describe_stream(StreamArn=arn)["StreamDescription"]
    except Exception as e:
        st.error(str(e))
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Status", desc.get("StreamStatus", "—"))
    c2.metric("View Type", desc.get("StreamViewType", "—"))
    c3.metric("Created", str(desc.get("CreationRequestDateTime", "—"))[:10])

    shards = desc.get("Shards", [])
    st.markdown(f"#### Shards ({len(shards)})")

    if not shards:
        st.info("No shards found.")
        return

    selected_shard = st.selectbox("Select shard to inspect", [s.get("ShardId", "—") for s in shards])
    shard = next((s for s in shards if s.get("ShardId") == selected_shard), None)

    if shard:
        c1, c2 = st.columns(2)
        c1.metric("Parent Shard", shard.get("ParentShardId", "—") or "Root")
        seq_range = shard.get("SequenceNumberRange", {})
        c2.metric("Starting Seq#", (seq_range.get("StartingSequenceNumber") or "—")[:16] + "…")

        if st.button("Fetch Recent Records"):
            try:
                iterator_resp = streams_client.get_shard_iterator(
                    StreamArn=arn,
                    ShardId=selected_shard,
                    ShardIteratorType="TRIM_HORIZON",
                )
                iterator = iterator_resp["ShardIterator"]
                records_resp = streams_client.get_records(ShardIterator=iterator, Limit=20)
                records = records_resp.get("Records", [])
                if records:
                    rows = [
                        {
                            "Event": r.get("eventName", "—"),
                            "Seq#": r.get("dynamodb", {}).get("SequenceNumber", "—")[:16] + "…",
                            "Keys": str(r.get("dynamodb", {}).get("Keys", {}))[:60],
                            "Approximate Time": str(r.get("dynamodb", {}).get("ApproximateCreationDateTime", "—"))[:19],
                        }
                        for r in records
                    ]
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                else:
                    st.info("No records in this shard (may be at end of stream).")
            except Exception as e:
                st.error(str(e))
