import streamlit as st
from aws_client import client


def _topic_name(arn: str) -> str:
    return arn.split(":")[-1]


def render():
    st.subheader("SNS")
    sns = client("sns")

    try:
        topics = sns.list_topics().get("Topics", [])
        all_subs = sns.list_subscriptions().get("Subscriptions", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not topics:
        st.info("No topics found.")
        return

    arn_map = {_topic_name(t["TopicArn"]): t["TopicArn"] for t in topics}
    selected_name = st.selectbox("Topic", list(arn_map.keys()))
    selected_arn = arn_map[selected_name]

    subs = [s for s in all_subs if s.get("TopicArn") == selected_arn]
    st.caption(f"{len(subs)} subscriptions")

    if subs:
        st.dataframe(
            [{"Protocol": s["Protocol"], "Endpoint": s["Endpoint"],
              "Status": "Pending" if s["SubscriptionArn"] == "PendingConfirmation" else "Confirmed"}
             for s in subs],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()
    st.markdown("**Publish**")
    subject = st.text_input("Subject (optional)", key="sns_subject")
    message = st.text_area("Message body", key="sns_body")
    if st.button("Publish", disabled=not message.strip()):
        try:
            kwargs = dict(TopicArn=selected_arn, Message=message.strip())
            if subject.strip():
                kwargs["Subject"] = subject.strip()
            sns.publish(**kwargs)
            st.success("✓ Published")
        except Exception as e:
            st.error(str(e))

