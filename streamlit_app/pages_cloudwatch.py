from datetime import datetime, timezone, timedelta
import streamlit as st
from aws_client import client


def render():
    st.subheader("📊 CloudWatch")
    cw = client("cloudwatch")

    try:
        ns_resp = cw.list_metrics()
        metrics = ns_resp.get("Metrics", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    namespaces = sorted({m["Namespace"] for m in metrics}) if metrics else []

    tab1, tab2 = st.tabs(["Metrics", "Alarms"])

    with tab1:
        if not namespaces:
            st.info("No metrics found.")
        else:
            col1, col2 = st.columns([6, 1])
            col1.caption(f"{len(metrics)} metric(s) across {len(namespaces)} namespace(s)")
            if col2.button("🔄 Refresh", use_container_width=True, key="cw_refresh"):
                st.rerun()

            ns = st.selectbox("Namespace", namespaces)
            ns_metrics = [m for m in metrics if m["Namespace"] == ns]
            metric_names = sorted({m["MetricName"] for m in ns_metrics})
            metric_name = st.selectbox("Metric", metric_names) if metric_names else None

            if metric_name:
                hours = st.slider("Time range (hours)", 1, 24, 3)
                end = datetime.now(tz=timezone.utc)
                start = end - timedelta(hours=hours)
                try:
                    stats = cw.get_metric_statistics(
                        Namespace=ns,
                        MetricName=metric_name,
                        StartTime=start,
                        EndTime=end,
                        Period=300,
                        Statistics=["Average", "Sum", "Maximum"],
                    )
                    datapoints = sorted(stats.get("Datapoints", []), key=lambda x: x["Timestamp"])
                    if datapoints:
                        rows = [
                            {
                                "Timestamp": str(dp["Timestamp"])[:19],
                                "Average": round(dp.get("Average", 0), 4),
                                "Sum": round(dp.get("Sum", 0), 4),
                                "Maximum": round(dp.get("Maximum", 0), 4),
                                "Unit": dp.get("Unit", "—"),
                            }
                            for dp in datapoints
                        ]
                        st.dataframe(rows, use_container_width=True, hide_index=True)
                    else:
                        st.info("No datapoints in this time range.")
                except Exception as e:
                    st.error(str(e))

    with tab2:
        try:
            alarms = cw.describe_alarms().get("MetricAlarms", [])
        except Exception as e:
            st.error(str(e))
            alarms = []

        if not alarms:
            st.info("No alarms configured.")
        else:
            st.caption(f"{len(alarms)} alarm(s)")
            rows = []
            for a in alarms:
                state = a.get("StateValue", "—")
                icon = "🟢" if state == "OK" else "🔴" if state == "ALARM" else "🟡"
                rows.append({
                    "Alarm": a.get("AlarmName", "—"),
                    "State": f"{icon} {state}",
                    "Metric": a.get("MetricName", "—"),
                    "Namespace": a.get("Namespace", "—"),
                    "Threshold": a.get("Threshold", "—"),
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)
