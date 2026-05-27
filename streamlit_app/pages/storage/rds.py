import streamlit as st
from aws_client import client


STATUS_ICONS = {
    "available": "🟢", "creating": "🟡", "deleting": "🟠",
    "failed": "🔴", "stopped": "⚫", "stopping": "🟠",
    "starting": "🟡", "modifying": "🟡", "rebooting": "🟡",
}


def render():
    st.subheader("🐘 RDS — Relational Database Service")
    rds = client("rds")

    if "rds_selected" not in st.session_state:
        st.session_state.rds_selected = None

    try:
        instances = rds.describe_db_instances().get("DBInstances", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    tab1, tab2 = st.tabs(["Instances", "Snapshots"])

    with tab1:
        if st.session_state.rds_selected is None:
            col1, col2 = st.columns([6, 1])
            col1.caption(f"{len(instances)} instance(s) found")
            if col2.button("🔄 Refresh", use_container_width=True):
                st.rerun()

            if not instances:
                st.info("No RDS instances found.")
            else:
                for db in instances:
                    dbid = db["DBInstanceIdentifier"]
                    status = db.get("DBInstanceStatus", "—")
                    icon = STATUS_ICONS.get(status, "⚪")
                    engine = db.get("Engine", "—")
                    engine_version = db.get("EngineVersion", "")
                    instance_class = db.get("DBInstanceClass", "—")

                    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
                    c1.markdown(f"**{dbid}**")
                    c2.caption(f"{icon} {status}")
                    c3.caption(f"{engine} {engine_version}")
                    c4.caption(instance_class)
                    if c5.button("View →", key=f"rds_btn_{dbid}"):
                        st.session_state.rds_selected = dbid
                        st.rerun()
        else:
            dbid = st.session_state.rds_selected
            db = next((d for d in instances if d["DBInstanceIdentifier"] == dbid), None)
            if not db:
                st.session_state.rds_selected = None
                st.rerun()

            if st.button("← Back to instances"):
                st.session_state.rds_selected = None
                st.rerun()

            status = db.get("DBInstanceStatus", "—")
            icon = STATUS_ICONS.get(status, "⚪")
            st.markdown(f"### {dbid}")
            st.caption(f"ARN: `{db.get('DBInstanceArn', '—')}`")

            c1, c2, c3 = st.columns(3)
            c1.metric("Status", f"{icon} {status}")
            c2.metric("Engine", f"{db.get('Engine','—')} {db.get('EngineVersion','')}")
            c3.metric("Class", db.get("DBInstanceClass", "—"))

            endpoint = db.get("Endpoint", {})
            if endpoint:
                c4, c5 = st.columns(2)
                c4.metric("Host", endpoint.get("Address", "—"))
                c5.metric("Port", endpoint.get("Port", "—"))

            with st.expander("Details"):
                fields = [
                    ("DB Name", db.get("DBName", "—")),
                    ("Master Username", db.get("MasterUsername", "—")),
                    ("Multi-AZ", str(db.get("MultiAZ", False))),
                    ("Storage Type", db.get("StorageType", "—")),
                    ("Allocated Storage (GiB)", db.get("AllocatedStorage", "—")),
                    ("Backup Retention (days)", db.get("BackupRetentionPeriod", "—")),
                    ("Created", str(db.get("InstanceCreateTime", "—"))[:19]),
                    ("Publicly Accessible", str(db.get("PubliclyAccessible", False))),
                ]
                st.dataframe([{"Field": f, "Value": v} for f, v in fields], use_container_width=True, hide_index=True)

    with tab2:
        try:
            snapshots = rds.describe_db_snapshots().get("DBSnapshots", [])
        except Exception as e:
            st.error(str(e))
            snapshots = []

        st.caption(f"{len(snapshots)} snapshot(s)")
        if snapshots:
            rows = [
                {
                    "Snapshot ID": s.get("DBSnapshotIdentifier", "—"),
                    "Instance": s.get("DBInstanceIdentifier", "—"),
                    "Status": s.get("Status", "—"),
                    "Engine": s.get("Engine", "—"),
                    "Size (GiB)": s.get("AllocatedStorage", "—"),
                    "Created": str(s.get("SnapshotCreateTime", "—"))[:10],
                    "Type": s.get("SnapshotType", "—"),
                }
                for s in snapshots
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No snapshots found.")
