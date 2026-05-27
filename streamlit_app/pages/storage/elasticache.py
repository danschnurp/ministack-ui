import streamlit as st
from aws_client import client


STATUS_ICONS = {
    "available": "🟢", "creating": "🟡", "deleting": "🟠",
    "modifying": "🟡", "rebooting cluster nodes": "🟡", "snapshotting": "🟡",
}


def render():
    st.subheader("🔴 ElastiCache — In-Memory Data Store")
    ec = client("elasticache")

    tab1, tab2 = st.tabs(["Clusters", "Replication Groups"])

    with tab1:
        try:
            clusters = ec.describe_cache_clusters(ShowCacheNodeInfo=True).get("CacheClusters", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            clusters = []

        if "ec_selected" not in st.session_state:
            st.session_state.ec_selected = None

        if st.session_state.ec_selected is None:
            col1, col2 = st.columns([6, 1])
            col1.caption(f"{len(clusters)} cluster(s) found")
            if col2.button("🔄 Refresh", key="ec_refresh", use_container_width=True):
                st.rerun()

            if not clusters:
                st.info("No ElastiCache clusters found.")
            else:
                for c in clusters:
                    cid = c["CacheClusterId"]
                    status = c.get("CacheClusterStatus", "—")
                    icon = STATUS_ICONS.get(status, "⚪")
                    engine = c.get("Engine", "—")
                    engine_version = c.get("EngineVersion", "")
                    node_type = c.get("CacheNodeType", "—")

                    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
                    c1.markdown(f"**{cid}**")
                    c2.caption(f"{icon} {status}")
                    c3.caption(f"{engine} {engine_version}")
                    c4.caption(node_type)
                    if c5.button("View →", key=f"ec_btn_{cid}"):
                        st.session_state.ec_selected = cid
                        st.rerun()
        else:
            cid = st.session_state.ec_selected
            cluster = next((c for c in clusters if c["CacheClusterId"] == cid), None)
            if not cluster:
                st.session_state.ec_selected = None
                st.rerun()

            if st.button("← Back to clusters"):
                st.session_state.ec_selected = None
                st.rerun()

            status = cluster.get("CacheClusterStatus", "—")
            icon = STATUS_ICONS.get(status, "⚪")
            st.markdown(f"### {cid}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Status", f"{icon} {status}")
            c2.metric("Engine", f"{cluster.get('Engine','—')} {cluster.get('EngineVersion','')}")
            c3.metric("Node Type", cluster.get("CacheNodeType", "—"))

            c4, c5 = st.columns(2)
            c4.metric("Num Nodes", cluster.get("NumCacheNodes", "—"))
            c5.metric("Created", str(cluster.get("CacheClusterCreateTime", "—"))[:10])

            nodes = cluster.get("CacheNodes", [])
            if nodes:
                with st.expander(f"Nodes ({len(nodes)})"):
                    rows = [
                        {
                            "Node ID": n.get("CacheNodeId", "—"),
                            "Status": n.get("CacheNodeStatus", "—"),
                            "Address": n.get("Endpoint", {}).get("Address", "—"),
                            "Port": n.get("Endpoint", {}).get("Port", "—"),
                            "Created": str(n.get("CacheNodeCreateTime", "—"))[:10],
                        }
                        for n in nodes
                    ]
                    st.dataframe(rows, use_container_width=True, hide_index=True)

    with tab2:
        try:
            rgs = ec.describe_replication_groups().get("ReplicationGroups", [])
        except Exception as e:
            st.error(str(e))
            rgs = []

        st.caption(f"{len(rgs)} replication group(s)")
        if rgs:
            rows = [
                {
                    "Group ID": rg.get("ReplicationGroupId", "—"),
                    "Description": rg.get("Description", "—"),
                    "Status": rg.get("Status", "—"),
                    "Cluster Enabled": "Yes" if rg.get("ClusterEnabled") else "No",
                    "Multi-AZ": rg.get("MultiAZ", "—"),
                    "Node Type": rg.get("CacheNodeType", "—"),
                }
                for rg in rgs
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No replication groups found.")
