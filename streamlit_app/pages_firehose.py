import streamlit as st
from aws_client import client


STATUS_ICON = {
    "ACTIVE": "🟢", "CREATING": "🟡", "DELETING": "🔴",
    "CREATING_FAILED": "🔴", "DELETING_FAILED": "🔴",
}


def render():
    st.subheader("🔥 Kinesis Firehose")
    fh = client("firehose")

    try:
        streams = fh.list_delivery_streams().get("DeliveryStreamNames", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not streams:
        st.info("No delivery streams found.")
        return

    if "firehose_selected" not in st.session_state:
        st.session_state.firehose_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.firehose_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(streams)} delivery stream(s)")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for name in streams:
            c1, c2 = st.columns([8, 1])
            c1.markdown(f"**{name}**")
            if c2.button("View →", key=f"fh_btn_{name}"):
                st.session_state.firehose_selected = name
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    selected = st.session_state.firehose_selected

    if st.button("← Back to list"):
        st.session_state.firehose_selected = None
        st.rerun()

    st.markdown(f"### {selected}")

    try:
        desc = fh.describe_delivery_stream(DeliveryStreamName=selected)["DeliveryStreamDescription"]
    except Exception as e:
        st.error(str(e))
        return

    status = desc.get("DeliveryStreamStatus", "—")
    icon = STATUS_ICON.get(status, "⚪")

    c1, c2, c3 = st.columns(3)
    c1.metric("Status", f"{icon} {status}")
    c2.metric("Type", desc.get("DeliveryStreamType", "—"))
    c3.metric("Created", str(desc.get("CreateTimestamp", "—"))[:10])

    with st.expander("Stream ARN"):
        st.code(desc.get("DeliveryStreamARN", ""), language="text")

    destinations = desc.get("Destinations", [])
    for i, dest in enumerate(destinations):
        with st.expander(f"Destination {i + 1}"):
            dest_id = dest.get("DestinationId", "—")
            st.caption(f"Destination ID: `{dest_id}`")

            if dest.get("S3DestinationDescription"):
                s3 = dest["S3DestinationDescription"]
                st.markdown("**→ S3**")
                st.dataframe([
                    {"Field": "Bucket ARN", "Value": s3.get("BucketARN", "—")},
                    {"Field": "Prefix", "Value": s3.get("Prefix", "—") or "(none)"},
                    {"Field": "Compression", "Value": s3.get("CompressionFormat", "—")},
                    {"Field": "Buffering (s)", "Value": s3.get("BufferingHints", {}).get("IntervalInSeconds", "—")},
                    {"Field": "Buffering (MB)", "Value": s3.get("BufferingHints", {}).get("SizeInMBs", "—")},
                ], use_container_width=True, hide_index=True)

            if dest.get("ExtendedS3DestinationDescription"):
                s3 = dest["ExtendedS3DestinationDescription"]
                st.markdown("**→ S3 (Extended)**")
                st.dataframe([
                    {"Field": "Bucket ARN", "Value": s3.get("BucketARN", "—")},
                    {"Field": "Role ARN", "Value": s3.get("RoleARN", "—")},
                    {"Field": "Compression", "Value": s3.get("CompressionFormat", "—")},
                ], use_container_width=True, hide_index=True)
