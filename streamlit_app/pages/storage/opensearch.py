import streamlit as st
from aws_client import client


STATUS_ICONS = {
    "Active": "🟢", "Creating": "🟡", "Deleting": "🟠",
    "Failed": "🔴", "Processing": "🟡", "Upgrading": "🟡",
}


def render():
    st.subheader("🔎 OpenSearch — Domains")
    oss = client("opensearch")

    if "oss_selected" not in st.session_state:
        st.session_state.oss_selected = None

    try:
        domain_names = [d["DomainName"] for d in oss.list_domain_names().get("DomainNames", [])]
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    domains = []
    if domain_names:
        try:
            domains = oss.describe_domains(DomainNames=domain_names).get("DomainStatusList", [])
        except Exception as e:
            st.error(str(e))
            return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.oss_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(domains)} domain(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not domains:
            st.info("No OpenSearch domains found.")
            return

        for d in domains:
            dname = d["DomainName"]
            processing = d.get("Processing", False)
            created = d.get("Created", False)
            deleted = d.get("Deleted", False)
            status = "Creating" if not created else "Deleting" if deleted else "Processing" if processing else "Active"
            icon = STATUS_ICONS.get(status, "⚪")
            engine_version = d.get("EngineVersion", "—")
            endpoint = d.get("Endpoint") or (list(d.get("Endpoints", {}).values()) or ["—"])[0]

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.markdown(f"**{dname}**")
            c2.caption(f"{icon} {status}")
            c3.caption(engine_version)
            c4.caption(str(endpoint)[:30])
            if c5.button("View →", key=f"oss_btn_{dname}"):
                st.session_state.oss_selected = dname
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    dname = st.session_state.oss_selected
    domain = next((d for d in domains if d["DomainName"] == dname), None)
    if not domain:
        st.session_state.oss_selected = None
        st.rerun()

    if st.button("← Back to domains"):
        st.session_state.oss_selected = None
        st.rerun()

    processing = domain.get("Processing", False)
    created = domain.get("Created", False)
    deleted = domain.get("Deleted", False)
    status = "Creating" if not created else "Deleting" if deleted else "Processing" if processing else "Active"
    icon = STATUS_ICONS.get(status, "⚪")

    st.markdown(f"### {dname}")
    st.caption(f"ARN: `{domain.get('ARN', '—')}`")

    endpoint = domain.get("Endpoint") or (list(domain.get("Endpoints", {}).values()) or ["—"])[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Status", f"{icon} {status}")
    c2.metric("Engine Version", domain.get("EngineVersion", "—"))
    c3.metric("Endpoint", str(endpoint)[:30])

    cluster_cfg = domain.get("ClusterConfig", {})
    c4, c5, c6 = st.columns(3)
    c4.metric("Instance Type", cluster_cfg.get("InstanceType", "—"))
    c5.metric("Instance Count", cluster_cfg.get("InstanceCount", "—"))
    c6.metric("Dedicated Master", "Yes" if cluster_cfg.get("DedicatedMasterEnabled") else "No")

    tab1, tab2 = st.tabs(["Configuration", "Access Policy"])

    with tab1:
        ebs = domain.get("EBSOptions", {})
        snap = domain.get("SnapshotOptions", {})
        encrypt = domain.get("EncryptionAtRestOptions", {})
        node_to_node = domain.get("NodeToNodeEncryptionOptions", {})

        st.dataframe([
            {"Field": "EBS Enabled", "Value": str(ebs.get("EBSEnabled", False))},
            {"Field": "EBS Volume Type", "Value": ebs.get("VolumeType", "—")},
            {"Field": "EBS Volume Size (GiB)", "Value": ebs.get("VolumeSize", "—")},
            {"Field": "Snapshot Hour (UTC)", "Value": snap.get("AutomatedSnapshotStartHour", "—")},
            {"Field": "Encryption at Rest", "Value": str(encrypt.get("Enabled", False))},
            {"Field": "Node-to-Node Encryption", "Value": str(node_to_node.get("Enabled", False))},
            {"Field": "Zone Awareness", "Value": str(cluster_cfg.get("ZoneAwarenessEnabled", False))},
        ], use_container_width=True, hide_index=True)

    with tab2:
        policy = domain.get("AccessPolicies", "")
        if policy:
            st.code(policy, language="json")
        else:
            st.info("No access policy set (open access or VPC-only).")
