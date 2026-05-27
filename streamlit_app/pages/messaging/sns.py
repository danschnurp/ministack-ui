import streamlit as st
from aws_client import client


def _topic_name(arn: str) -> str:
    return arn.split(":")[-1]


def render():
    st.subheader("📣 SNS")
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

    if "sns_selected" not in st.session_state:
        st.session_state.sns_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.sns_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(arn_map)} topic(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for name in arn_map:
            c1, c2 = st.columns([8, 1])
            c1.markdown(f"**{name}**")
            if c2.button("View →", key=f"sns_btn_{name}"):
                st.session_state.sns_selected = name
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    selected_name = st.session_state.sns_selected
    selected_arn = arn_map.get(selected_name)
    if not selected_arn:
        st.session_state.sns_selected = None
        st.rerun()

    if st.button("← Back to list"):
        st.session_state.sns_selected = None
        st.rerun()

    st.markdown(f"### {selected_name}")

    try:
        attrs = sns.get_topic_attributes(TopicArn=selected_arn).get("Attributes", {})
    except Exception:
        attrs = {}

    c1, c2, c3 = st.columns(3)
    c1.metric("Subscriptions Confirmed", attrs.get("SubscriptionsConfirmed", "—"))
    c2.metric("Subscriptions Pending", attrs.get("SubscriptionsPending", "—"))
    c3.metric("Subscriptions Deleted", attrs.get("SubscriptionsDeleted", "—"))

    with st.expander("Topic ARN"):
        st.code(selected_arn, language="text")

    st.divider()

    subs = [s for s in all_subs if s.get("TopicArn") == selected_arn]
    st.markdown(f"**Subscriptions** ({len(subs)})")

    if subs:
        st.dataframe(
            [
                {
                    "Protocol": s["Protocol"],
                    "Endpoint": s["Endpoint"] or "—",
                    "Status": "⏳ Pending" if s["SubscriptionArn"] == "PendingConfirmation" else "✅ Confirmed",
                    "Subscription ARN": s["SubscriptionArn"][:40] + "…" if len(s.get("SubscriptionArn", "")) > 40 else s.get("SubscriptionArn", "—"),
                }
                for s in subs
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No subscriptions for this topic.")

    st.divider()

    st.markdown("**Publish Message**")
    subject = st.text_input("Subject (optional)", key="sns_subject", placeholder="e.g. Alert: Disk Usage High")
    message = st.text_area("Message body", key="sns_body", placeholder="Enter your message…", height=120)

    with st.expander("Message Attributes (optional)"):
        attr_key = st.text_input("Attribute key", key="sns_attr_key", placeholder="e.g. event-type")
        attr_val = st.text_input("Attribute value (String)", key="sns_attr_val", placeholder="e.g. order-placed")

    if st.button("📤 Publish", disabled=not message.strip()):
        try:
            kwargs = dict(TopicArn=selected_arn, Message=message.strip())
            if subject.strip():
                kwargs["Subject"] = subject.strip()
            if attr_key.strip() and attr_val.strip():
                kwargs["MessageAttributes"] = {
                    attr_key.strip(): {"DataType": "String", "StringValue": attr_val.strip()}
                }
            resp = sns.publish(**kwargs)
            st.success(f"✓ Published — Message ID: `{resp['MessageId']}`")
        except Exception as e:
            st.error(str(e))
