import streamlit as st
from aws_client import client


def render():
    st.subheader("📜 CloudTrail — Audit Logging")
    ct = client("cloudtrail")

    tab1, tab2 = st.tabs(["Trails", "Recent Events"])

    with tab1:
        try:
            trails = ct.describe_trails(includeShadowTrails=False).get("trailList", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            trails = []

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(trails)} trail(s) found")
        if col2.button("🔄 Refresh", key="ct_refresh", use_container_width=True):
            st.rerun()

        if not trails:
            st.info("No CloudTrail trails found.")
        else:
            for trail in trails:
                name = trail.get("Name", "—")
                s3 = trail.get("S3BucketName", "—")
                multi_region = "🌍 Multi-region" if trail.get("IsMultiRegionTrail") else "📍 Single-region"
                log_enabled = trail.get("LogFileValidationEnabled", False)

                with st.expander(f"**{name}**"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("S3 Bucket", s3)
                    c2.metric("Scope", multi_region)
                    c3.metric("Log Validation", "✅" if log_enabled else "❌")

                    st.dataframe([
                        {"Field": "Trail ARN", "Value": trail.get("TrailARN", "—")},
                        {"Field": "Home Region", "Value": trail.get("HomeRegion", "—")},
                        {"Field": "Log Group ARN", "Value": trail.get("CloudWatchLogsLogGroupArn", "—") or "—"},
                        {"Field": "S3 Key Prefix", "Value": trail.get("S3KeyPrefix", "—") or "/"},
                        {"Field": "SNS Topic", "Value": trail.get("SnsTopicName", "—") or "—"},
                        {"Field": "Global Service Events", "Value": str(trail.get("IncludeGlobalServiceEvents", False))},
                    ], use_container_width=True, hide_index=True)

                    try:
                        status = ct.get_trail_status(Name=name)
                        logging_on = status.get("IsLogging", False)
                        latest_delivery = str(status.get("LatestDeliveryTime", "—"))[:19]
                        st.info(f"Logging: {'🟢 ON' if logging_on else '🔴 OFF'}  |  Latest delivery: {latest_delivery}")
                    except Exception:
                        pass

    with tab2:
        st.markdown("#### Lookup Recent Events")
        col_a, col_b, col_c = st.columns([4, 2, 1])
        attr_key = col_a.selectbox("Attribute", [
            "EventName", "Username", "ResourceName", "ResourceType",
            "EventSource", "ReadOnly", "EventId", "AccessKeyId",
        ])
        attr_val = col_b.text_input("Value", placeholder="e.g. CreateBucket")
        max_results = 20

        if col_c.button("Search", use_container_width=True):
            try:
                kwargs = {}
                if attr_val:
                    kwargs["LookupAttributes"] = [{"AttributeKey": attr_key, "AttributeValue": attr_val}]
                events = ct.lookup_events(MaxResults=max_results, **kwargs).get("Events", [])
                if events:
                    rows = [
                        {
                            "Time": str(e.get("EventTime", "—"))[:19],
                            "Event": e.get("EventName", "—"),
                            "User": e.get("Username", "—"),
                            "Source": e.get("EventSource", "—"),
                            "Resources": ", ".join(r.get("ResourceName", "") for r in e.get("Resources", [])),
                        }
                        for e in events
                    ]
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                else:
                    st.info("No events found.")
            except Exception as e:
                st.error(str(e))
        else:
            try:
                events = ct.lookup_events(MaxResults=max_results).get("Events", [])
                if events:
                    rows = [
                        {
                            "Time": str(e.get("EventTime", "—"))[:19],
                            "Event": e.get("EventName", "—"),
                            "User": e.get("Username", "—"),
                            "Source": e.get("EventSource", "—"),
                        }
                        for e in events
                    ]
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                else:
                    st.info("No recent events found.")
            except Exception as e:
                st.error(f"Failed to fetch events: {e}")
