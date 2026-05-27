import streamlit as st
from aws_client import client


STATE_ICONS = {
    "available": "🟢", "in-use": "🔵", "creating": "🟡",
    "deleting": "🟠", "deleted": "⚫", "error": "🔴",
}

SNAPSHOT_STATE_ICONS = {
    "completed": "🟢", "pending": "🟡", "error": "🔴",
}


def render():
    st.subheader("💾 EBS — Elastic Block Store")
    ec2 = client("ec2")

    tab1, tab2 = st.tabs(["Volumes", "Snapshots"])

    with tab1:
        try:
            volumes = ec2.describe_volumes().get("Volumes", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            volumes = []

        if "ebs_selected" not in st.session_state:
            st.session_state.ebs_selected = None

        if st.session_state.ebs_selected is None:
            col1, col2 = st.columns([6, 1])
            col1.caption(f"{len(volumes)} volume(s) found")
            if col2.button("🔄 Refresh", key="ebs_refresh", use_container_width=True):
                st.rerun()

            if not volumes:
                st.info("No EBS volumes found.")
            else:
                for v in volumes:
                    vid = v["VolumeId"]
                    state = v.get("State", "—")
                    icon = STATE_ICONS.get(state, "⚪")
                    vtype = v.get("VolumeType", "—")
                    size = v.get("Size", "—")
                    name = next((t["Value"] for t in v.get("Tags", []) if t["Key"] == "Name"), "—")
                    attachments = v.get("Attachments", [])
                    attached_to = attachments[0].get("InstanceId", "—") if attachments else "—"

                    c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1, 2, 2, 1])
                    c1.markdown(f"**{vid}**")
                    c2.caption(name)
                    c3.caption(f"{icon} {state}")
                    c4.caption(f"{vtype} · {size} GiB")
                    c5.caption(f"→ {attached_to}")
                    if c6.button("View →", key=f"ebs_btn_{vid}"):
                        st.session_state.ebs_selected = vid
                        st.rerun()
        else:
            vid = st.session_state.ebs_selected
            vol = next((v for v in volumes if v["VolumeId"] == vid), None)
            if not vol:
                st.session_state.ebs_selected = None
                st.rerun()

            if st.button("← Back to volumes"):
                st.session_state.ebs_selected = None
                st.rerun()

            state = vol.get("State", "—")
            icon = STATE_ICONS.get(state, "⚪")
            name = next((t["Value"] for t in vol.get("Tags", []) if t["Key"] == "Name"), vid)
            st.markdown(f"### {name}")
            st.caption(f"Volume ID: `{vid}`")

            c1, c2, c3 = st.columns(3)
            c1.metric("State", f"{icon} {state}")
            c2.metric("Type", vol.get("VolumeType", "—"))
            c3.metric("Size", f"{vol.get('Size', '—')} GiB")

            c4, c5, c6 = st.columns(3)
            c4.metric("IOPS", vol.get("Iops", "—"))
            c5.metric("Throughput (MiB/s)", vol.get("Throughput", "—"))
            c6.metric("Encrypted", "Yes" if vol.get("Encrypted") else "No")

            attachments = vol.get("Attachments", [])
            if attachments:
                with st.expander(f"Attachments ({len(attachments)})"):
                    rows = [
                        {
                            "Instance ID": a.get("InstanceId", "—"),
                            "Device": a.get("Device", "—"),
                            "State": a.get("State", "—"),
                            "Delete on Termination": str(a.get("DeleteOnTermination", False)),
                        }
                        for a in attachments
                    ]
                    st.dataframe(rows, use_container_width=True, hide_index=True)

    with tab2:
        try:
            snapshots = ec2.describe_snapshots(OwnerIds=["self"]).get("Snapshots", [])
        except Exception as e:
            st.error(str(e))
            snapshots = []

        st.caption(f"{len(snapshots)} snapshot(s)")
        if col2 := st.columns([6, 1])[1]:
            if col2.button("🔄 Refresh", key="ebs_snap_refresh", use_container_width=True):
                st.rerun()

        if snapshots:
            rows = [
                {
                    "Snapshot ID": s.get("SnapshotId", "—"),
                    "Volume ID": s.get("VolumeId", "—"),
                    "State": s.get("State", "—"),
                    "Size (GiB)": s.get("VolumeSize", "—"),
                    "Description": s.get("Description", "—")[:40],
                    "Started": str(s.get("StartTime", "—"))[:10],
                    "Encrypted": "Yes" if s.get("Encrypted") else "No",
                }
                for s in snapshots
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("No snapshots found.")
