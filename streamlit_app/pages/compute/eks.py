import streamlit as st
from aws_client import client


STATUS_ICONS = {
    "ACTIVE": "🟢", "CREATING": "🟡", "DELETING": "🔴",
    "FAILED": "🔴", "UPDATING": "🟡", "DEGRADED": "🟠",
}


def render():
    st.subheader("☸️ EKS — Elastic Kubernetes Service")
    eks = client("eks")

    if "eks_selected" not in st.session_state:
        st.session_state.eks_selected = None

    try:
        cluster_names = eks.list_clusters().get("clusters", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.eks_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(cluster_names)} cluster(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not cluster_names:
            st.info("No EKS clusters found.")
            return

        for cname in cluster_names:
            try:
                c = eks.describe_cluster(name=cname)["cluster"]
                status = c.get("status", "—")
                icon = STATUS_ICONS.get(status, "⚪")
                version = c.get("version", "—")
                endpoint = c.get("endpoint", "—") or "—"
                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
                c1.markdown(f"**{cname}**")
                c2.caption(f"{icon} {status}")
                c3.caption(f"k8s {version}")
                c4.caption(endpoint[:30])
                if c5.button("View →", key=f"eks_btn_{cname}"):
                    st.session_state.eks_selected = cname
                    st.rerun()
            except Exception:
                c1, c2 = st.columns([8, 1])
                c1.markdown(f"**{cname}**")
                if c2.button("View →", key=f"eks_btn_{cname}"):
                    st.session_state.eks_selected = cname
                    st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    cname = st.session_state.eks_selected

    if st.button("← Back to clusters"):
        st.session_state.eks_selected = None
        st.rerun()

    try:
        cluster = eks.describe_cluster(name=cname)["cluster"]
    except Exception as e:
        st.error(str(e))
        return

    status = cluster.get("status", "—")
    icon = STATUS_ICONS.get(status, "⚪")
    st.markdown(f"### {cname}")
    st.caption(f"ARN: `{cluster.get('arn', '—')}`")

    c1, c2, c3 = st.columns(3)
    c1.metric("Status", f"{icon} {status}")
    c2.metric("Kubernetes Version", cluster.get("version", "—"))
    c3.metric("Role ARN", (cluster.get("roleArn") or "—")[-30:] + "…")

    if cluster.get("endpoint"):
        st.code(cluster["endpoint"], language="text")

    tab1, tab2, tab3 = st.tabs(["Node Groups", "Fargate Profiles", "Add-ons"])

    with tab1:
        try:
            ngs = eks.list_nodegroups(clusterName=cname).get("nodegroups", [])
            if ngs:
                rows = []
                for ng_name in ngs:
                    try:
                        ng = eks.describe_nodegroup(clusterName=cname, nodegroupName=ng_name)["nodegroup"]
                        rows.append({
                            "Node Group": ng_name,
                            "Status": ng.get("status", "—"),
                            "AMI Type": ng.get("amiType", "—"),
                            "Instance Types": ", ".join(ng.get("instanceTypes", [])),
                            "Desired": ng.get("scalingConfig", {}).get("desiredSize", "—"),
                            "Min": ng.get("scalingConfig", {}).get("minSize", "—"),
                            "Max": ng.get("scalingConfig", {}).get("maxSize", "—"),
                        })
                    except Exception:
                        rows.append({"Node Group": ng_name, "Status": "—"})
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No node groups found.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        try:
            profiles = eks.list_fargate_profiles(clusterName=cname).get("fargateProfileNames", [])
            if profiles:
                st.dataframe(
                    [{"Fargate Profile": p} for p in profiles],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No Fargate profiles found.")
        except Exception as e:
            st.error(str(e))

    with tab3:
        try:
            addons = eks.list_addons(clusterName=cname).get("addons", [])
            if addons:
                rows = []
                for addon_name in addons:
                    try:
                        a = eks.describe_addon(clusterName=cname, addonName=addon_name)["addon"]
                        rows.append({
                            "Add-on": addon_name,
                            "Status": a.get("status", "—"),
                            "Version": a.get("addonVersion", "—"),
                        })
                    except Exception:
                        rows.append({"Add-on": addon_name})
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No add-ons installed.")
        except Exception as e:
            st.error(str(e))
