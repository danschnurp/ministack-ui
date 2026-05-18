import streamlit as st
from aws_client import client


def render():
    st.subheader("Kinesis")
    kin = client("kinesis")

    try:
        streams = kin.list_streams()["StreamNames"]
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not streams:
        st.info("No streams found.")
        return

    selected = st.selectbox("Stream", streams)

    if selected:
        try:
            summary = kin.describe_stream_summary(StreamName=selected)["StreamDescriptionSummary"]
            shards = kin.list_shards(StreamName=selected)["Shards"]
        except Exception as e:
            st.error(str(e))
            return

        status = summary.get("StreamStatus", "")
        color = "🟢" if status == "ACTIVE" else "🔵"
        st.markdown(f"{color} **{status}**")

        st.dataframe(
            [{"Field": k, "Value": str(summary.get(k, ""))}
             for k in ("StreamARN", "RetentionPeriodHours", "OpenShardCount", "EncryptionType")],
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("**Shards**")
        st.dataframe(
            [{"Shard ID": s["ShardId"],
              "Starting key": s["HashKeyRange"]["StartingHashKey"][:12] + "…",
              "Ending key": s["HashKeyRange"]["EndingHashKey"][:12] + "…"}
             for s in shards],
            use_container_width=True,
            hide_index=True,
        )

