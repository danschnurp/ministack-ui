from datetime import datetime
import streamlit as st
from aws_client import client


def render():
    st.subheader("CloudWatch Logs")
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
    selected_group = st.selectbox("Log Group", group_names)

    if selected_group:
        stream = st.text_input("Log Stream name", placeholder="e.g. my-stream")

        if stream:
            try:
                events = logs.get_log_events(
                    logGroupName=selected_group,
                    logStreamName=stream,
                    startFromHead=True,
                ).get("events", [])
            except Exception as e:
                st.error(str(e))
                return

            if not events:
                st.info("No events found.")
                return

            lines = []
            for e in events:
                ts = datetime.fromtimestamp(e["timestamp"] / 1000).isoformat() if e.get("timestamp") else "—"
                lines.append(f"{ts}  {e.get('message', '')}")

            st.code("\n".join(lines), language="text")

