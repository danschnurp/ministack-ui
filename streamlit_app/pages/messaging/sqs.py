import streamlit as st
from aws_client import client


def _queue_name(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def render():
    st.subheader("📨 SQS")
    sqs = client("sqs")

    try:
        queues = sqs.list_queues().get("QueueUrls", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not queues:
        st.info("No queues found.")
        return

    queue_map = {_queue_name(q): q for q in queues}

    if "sqs_selected" not in st.session_state:
        st.session_state.sqs_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.sqs_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(queue_map)} queue(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for name in queue_map:
            c1, c2 = st.columns([8, 1])
            c1.markdown(f"**{name}**")
            if c2.button("View →", key=f"sqs_btn_{name}"):
                st.session_state.sqs_selected = name
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    selected_name = st.session_state.sqs_selected
    selected = queue_map.get(selected_name)
    if not selected:
        st.session_state.sqs_selected = None
        st.rerun()

    if st.button("← Back to list"):
        st.session_state.sqs_selected = None
        st.rerun()

    st.markdown(f"### {selected_name}")

    try:
        attributes = sqs.get_queue_attributes(
            QueueUrl=selected, AttributeNames=["All"]
        ).get("Attributes", {})
    except Exception as e:
        st.error(str(e))
        return

    approx = attributes.get("ApproximateNumberOfMessages", "—")
    in_flight = attributes.get("ApproximateNumberOfMessagesNotVisible", "—")
    delayed = attributes.get("ApproximateNumberOfMessagesDelayed", "—")
    visibility = attributes.get("VisibilityTimeout", "—")
    retention = attributes.get("MessageRetentionPeriod", "—")
    is_fifo = attributes.get("FifoQueue", "false") == "true"

    c1, c2, c3 = st.columns(3)
    c1.metric("Messages Available", approx)
    c2.metric("In-flight", in_flight)
    c3.metric("Delayed", delayed)

    c4, c5, c6 = st.columns(3)
    c4.metric("Visibility Timeout", f"{visibility}s")
    c5.metric("Retention Period", f"{int(retention) // 3600}h" if retention != "—" else "—")
    c6.metric("Type", "FIFO 📋" if is_fifo else "Standard")

    st.divider()
    with st.expander("Queue URL"):
        st.code(selected, language="text")
    with st.expander("All Attributes (JSON)"):
        st.json(attributes)

    st.divider()
    st.markdown("**Send Message**")
    msg_body = st.text_area("Message body", key="sqs_body", placeholder="Enter message content…")
    send_cols = st.columns([2, 1])
    with send_cols[0]:
        delay_sec = st.number_input("Delay (seconds)", min_value=0, max_value=900, value=0, key="sqs_delay")
    with send_cols[1]:
        st.write("")
        st.write("")
        send = st.button("Send", disabled=not msg_body.strip(), use_container_width=True)

    if send:
        try:
            resp = sqs.send_message(
                QueueUrl=selected,
                MessageBody=msg_body.strip(),
                DelaySeconds=int(delay_sec),
            )
            st.success(f"✓ Message sent — ID: `{resp['MessageId']}`")
        except Exception as e:
            st.error(str(e))
