import streamlit as st
from aws_client import client


def render():
    st.subheader("🐳 ECS — Elastic Container Service")
    ecs = client("ecs")

    if "ecs_cluster_selected" not in st.session_state:
        st.session_state.ecs_cluster_selected = None

    try:
        cluster_arns = ecs.list_clusters().get("clusterArns", [])
        clusters = ecs.describe_clusters(clusters=cluster_arns).get("clusters", []) if cluster_arns else []
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.ecs_cluster_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(clusters)} cluster(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not clusters:
            st.info("No ECS clusters found.")
            return

        for c in clusters:
            arn = c["clusterArn"]
            name = c.get("clusterName", "—")
            status = c.get("status", "—")
            icon = "🟢" if status == "ACTIVE" else "🔴"
            svc_count = c.get("activeServicesCount", 0)
            task_count = c.get("runningTasksCount", 0)

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.markdown(f"**{name}**")
            c2.caption(f"{icon} {status}")
            c3.caption(f"{svc_count} services")
            c4.caption(f"{task_count} running tasks")
            if c5.button("View →", key=f"ecs_btn_{arn}"):
                st.session_state.ecs_cluster_selected = arn
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    arn = st.session_state.ecs_cluster_selected
    cluster = next((c for c in clusters if c["clusterArn"] == arn), None)
    if not cluster:
        st.session_state.ecs_cluster_selected = None
        st.rerun()

    if st.button("← Back to clusters"):
        st.session_state.ecs_cluster_selected = None
        st.rerun()

    name = cluster.get("clusterName", "—")
    status = cluster.get("status", "—")
    icon = "🟢" if status == "ACTIVE" else "🔴"
    st.markdown(f"### {name}")
    st.caption(f"ARN: `{arn}`")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", f"{icon} {status}")
    c2.metric("Active Services", cluster.get("activeServicesCount", 0))
    c3.metric("Running Tasks", cluster.get("runningTasksCount", 0))
    c4.metric("Pending Tasks", cluster.get("pendingTasksCount", 0))

    tab1, tab2, tab3 = st.tabs(["Services", "Tasks", "Task Definitions"])

    with tab1:
        try:
            svc_arns = ecs.list_services(cluster=arn).get("serviceArns", [])
            svcs = ecs.describe_services(cluster=arn, services=svc_arns).get("services", []) if svc_arns else []
            if svcs:
                rows = [
                    {
                        "Service": s.get("serviceName", "—"),
                        "Status": s.get("status", "—"),
                        "Desired": s.get("desiredCount", 0),
                        "Running": s.get("runningCount", 0),
                        "Pending": s.get("pendingCount", 0),
                        "Launch Type": s.get("launchType", "—"),
                    }
                    for s in svcs
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No services found.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        try:
            task_arns = ecs.list_tasks(cluster=arn).get("taskArns", [])
            tasks = ecs.describe_tasks(cluster=arn, tasks=task_arns).get("tasks", []) if task_arns else []
            if tasks:
                rows = [
                    {
                        "Task ID": t.get("taskArn", "—").split("/")[-1][:12] + "…",
                        "Last Status": t.get("lastStatus", "—"),
                        "Desired Status": t.get("desiredStatus", "—"),
                        "Launch Type": t.get("launchType", "—"),
                        "CPU": t.get("cpu", "—"),
                        "Memory": t.get("memory", "—"),
                        "Started At": str(t.get("startedAt", "—"))[:19],
                    }
                    for t in tasks
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No running tasks.")
        except Exception as e:
            st.error(str(e))

    with tab3:
        try:
            td_arns = ecs.list_task_definitions().get("taskDefinitionArns", [])
            if td_arns:
                st.dataframe(
                    [{"Task Definition": a.split("/")[-1]} for a in td_arns],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No task definitions found.")
        except Exception as e:
            st.error(str(e))
