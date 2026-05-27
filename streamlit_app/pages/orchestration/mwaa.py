import streamlit as st
from aws_client import client


STATUS_ICONS = {
    "AVAILABLE": "🟢", "CREATING": "🟡", "DELETING": "🟠",
    "UPDATING": "🟡", "UNAVAILABLE": "🔴", "CREATE_FAILED": "🔴",
}


def render():
    st.subheader("🪁 MWAA — Managed Apache Airflow")
    mwaa = client("mwaa")

    if "mwaa_selected" not in st.session_state:
        st.session_state.mwaa_selected = None

    try:
        env_names = mwaa.list_environments().get("Environments", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.mwaa_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(env_names)} environment(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not env_names:
            st.info("No MWAA environments found.")
            return

        for name in env_names:
            try:
                env = mwaa.get_environment(Name=name)["Environment"]
                status = env.get("Status", "—")
                icon = STATUS_ICONS.get(status, "⚪")
                version = env.get("AirflowVersion", "—")
                dag_s3 = env.get("DagS3Path", "—")

                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
                c1.markdown(f"**{name}**")
                c2.caption(f"{icon} {status}")
                c3.caption(f"Airflow {version}")
                c4.caption(dag_s3[:30])
                if c5.button("View →", key=f"mwaa_btn_{name}"):
                    st.session_state.mwaa_selected = name
                    st.rerun()
            except Exception:
                c1, c2 = st.columns([8, 1])
                c1.markdown(f"**{name}**")
                if c2.button("View →", key=f"mwaa_btn_{name}"):
                    st.session_state.mwaa_selected = name
                    st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    name = st.session_state.mwaa_selected

    if st.button("← Back to environments"):
        st.session_state.mwaa_selected = None
        st.rerun()

    try:
        env = mwaa.get_environment(Name=name)["Environment"]
    except Exception as e:
        st.error(str(e))
        return

    status = env.get("Status", "—")
    icon = STATUS_ICONS.get(status, "⚪")
    st.markdown(f"### {name}")
    st.caption(f"ARN: `{env.get('Arn', '—')}`")

    c1, c2, c3 = st.columns(3)
    c1.metric("Status", f"{icon} {status}")
    c2.metric("Airflow Version", env.get("AirflowVersion", "—"))
    c3.metric("Environment Class", env.get("EnvironmentClass", "—"))

    if env.get("WebserverUrl"):
        st.markdown(f"**Airflow UI:** [{env['WebserverUrl']}]({env['WebserverUrl']})")

    tab1, tab2 = st.tabs(["Configuration", "Logging"])

    with tab1:
        network = env.get("NetworkConfiguration", {})
        st.dataframe([
            {"Field": "DAG S3 Path", "Value": env.get("DagS3Path", "—")},
            {"Field": "S3 Bucket", "Value": env.get("SourceBucketArn", "—")},
            {"Field": "Plugins S3", "Value": env.get("PluginsS3Path", "—") or "—"},
            {"Field": "Requirements S3", "Value": env.get("RequirementsS3Path", "—") or "—"},
            {"Field": "Max Workers", "Value": env.get("MaxWorkers", "—")},
            {"Field": "Min Workers", "Value": env.get("MinWorkers", "—")},
            {"Field": "Schedulers", "Value": env.get("Schedulers", "—")},
            {"Field": "Subnets", "Value": ", ".join(network.get("SubnetIds", []))},
            {"Field": "Security Groups", "Value": ", ".join(network.get("SecurityGroupIds", []))},
        ], use_container_width=True, hide_index=True)

    with tab2:
        logging_conf = env.get("LoggingConfiguration", {})
        if logging_conf:
            rows = [
                {"Log Type": k, "Enabled": str(v.get("Enabled", False)), "Level": v.get("LogLevel", "—")}
                for k, v in logging_conf.items()
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No logging configuration found.")
