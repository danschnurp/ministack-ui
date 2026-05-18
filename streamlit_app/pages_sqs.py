import streamlit as st
from aws_client import client


def render():
    st.subheader("SQS")
    sqs = client("sqs")

    try:
        queues = sqs.list_queues().get("QueueUrls", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not queues:
        st.info("No queues found.")
        return

    selected = st.selectbox("Queue", queues)

    if selected:
        try:
            attributes = sqs.get_queue_attributes(
                QueueUrl=selected, AttributeNames=["All"]
            ).get("Attributes", {})
        except Exception as e:
            st.error(str(e))
            return

        st.caption(f"Queue URL: {selected}")
        st.json(attributes)
