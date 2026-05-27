import streamlit as st
from aws_client import client


STATE_ICONS = {
    "available": "🟢", "creating": "🟡", "deleting": "🟠",
    "deleted": "⚫", "error": "🔴", "updating": "🟡",
}


def render():
    st.subheader("📁 EFS — Elastic File System")
    efs = client("efs")

    if "efs_selected" not in st.session_state:
        st.session_state.efs_selected = None

    try:
        filesystems = efs.describe_file_systems().get("FileSystems", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.efs_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(filesystems)} file system(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not filesystems:
            st.info("No EFS file systems found.")
            return

        for fs in filesystems:
            fsid = fs["FileSystemId"]
            state = fs.get("LifeCycleState", "—")
            icon = STATE_ICONS.get(state, "⚪")
            name = fs.get("Name") or next((t["Value"] for t in fs.get("Tags", []) if t["Key"] == "Name"), "—")
            size_bytes = fs.get("SizeInBytes", {}).get("Value", 0)
            size_str = f"{size_bytes / (1024**3):.2f} GiB" if size_bytes else "0 GiB"

            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
            c1.markdown(f"**{name}**")
            c2.caption(f"{icon} {state}")
            c3.caption(fs.get("PerformanceMode", "—"))
            c4.caption(size_str)
            if c5.button("View →", key=f"efs_btn_{fsid}"):
                st.session_state.efs_selected = fsid
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    fsid = st.session_state.efs_selected
    fs = next((f for f in filesystems if f["FileSystemId"] == fsid), None)
    if not fs:
        st.session_state.efs_selected = None
        st.rerun()

    if st.button("← Back to file systems"):
        st.session_state.efs_selected = None
        st.rerun()

    state = fs.get("LifeCycleState", "—")
    icon = STATE_ICONS.get(state, "⚪")
    name = fs.get("Name") or next((t["Value"] for t in fs.get("Tags", []) if t["Key"] == "Name"), fsid)
    st.markdown(f"### {name}")
    st.caption(f"File System ID: `{fsid}`  |  ARN: `{fs.get('FileSystemArn', '—')}`")

    size_bytes = fs.get("SizeInBytes", {}).get("Value", 0)
    c1, c2, c3 = st.columns(3)
    c1.metric("State", f"{icon} {state}")
    c2.metric("Performance Mode", fs.get("PerformanceMode", "—"))
    c3.metric("Size", f"{size_bytes / (1024**3):.2f} GiB")

    c4, c5, c6 = st.columns(3)
    c4.metric("Throughput Mode", fs.get("ThroughputMode", "—"))
    c5.metric("Encrypted", "Yes" if fs.get("Encrypted") else "No")
    c6.metric("Created", str(fs.get("CreationTime", "—"))[:10])

    tab1, tab2, tab3 = st.tabs(["Mount Targets", "Access Points", "Lifecycle Policy"])

    with tab1:
        try:
            mts = efs.describe_mount_targets(FileSystemId=fsid).get("MountTargets", [])
            if mts:
                rows = [
                    {
                        "Mount Target ID": mt.get("MountTargetId", "—"),
                        "State": mt.get("LifeCycleState", "—"),
                        "IP Address": mt.get("IpAddress", "—"),
                        "Subnet ID": mt.get("SubnetId", "—"),
                        "AZ": mt.get("AvailabilityZoneName", "—"),
                    }
                    for mt in mts
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No mount targets found.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        try:
            aps = efs.describe_access_points(FileSystemId=fsid).get("AccessPoints", [])
            if aps:
                rows = [
                    {
                        "Access Point ID": ap.get("AccessPointId", "—"),
                        "Name": next((t["Value"] for t in ap.get("Tags", []) if t["Key"] == "Name"), "—"),
                        "State": ap.get("LifeCycleState", "—"),
                        "Root Path": ap.get("RootDirectory", {}).get("Path", "/"),
                        "POSIX UID": ap.get("PosixUser", {}).get("Uid", "—"),
                    }
                    for ap in aps
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No access points found.")
        except Exception as e:
            st.error(str(e))

    with tab3:
        try:
            lcp = efs.describe_lifecycle_configuration(FileSystemId=fsid).get("LifecyclePolicies", [])
            if lcp:
                st.dataframe(
                    [{"Policy": str(p)} for p in lcp],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No lifecycle policies configured.")
        except Exception as e:
            st.error(str(e))
