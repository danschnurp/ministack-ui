import streamlit as st
from aws_client import client


def fmt_size(b: int) -> str:
    if b >= 1_073_741_824:
        return f"{b / 1_073_741_824:.2f} GB"
    if b >= 1_048_576:
        return f"{b / 1_048_576:.1f} MB"
    if b >= 1024:
        return f"{b // 1024} KB"
    return f"{b} B"


def render():
    st.subheader("🪣 S3")
    s3 = client("s3")

    try:
        buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not buckets:
        st.info("No buckets found.")
        return

    if "s3_selected" not in st.session_state:
        st.session_state.s3_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.s3_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(buckets)} bucket(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for name in buckets:
            c1, c2 = st.columns([8, 1])
            c1.markdown(f"**{name}**")
            if c2.button("View →", key=f"s3_btn_{name}"):
                st.session_state.s3_selected = name
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    selected = st.session_state.s3_selected

    if st.button("← Back to list"):
        st.session_state.s3_selected = None
        st.rerun()

    st.markdown(f"### {selected}")

    try:
        resp = s3.list_objects_v2(Bucket=selected)
        objects = resp.get("Contents", [])
        is_truncated = resp.get("IsTruncated", False)
    except Exception as e:
        st.error(str(e))
        return

    total_size = sum(o["Size"] for o in objects)
    c1, c2, c3 = st.columns(3)
    c1.metric("Objects", len(objects))
    c2.metric("Total Size", fmt_size(total_size))
    c3.metric("Truncated", "Yes ⚠️" if is_truncated else "No")

    if objects:
        search = st.text_input("🔍 Filter by key prefix", placeholder="e.g. logs/")
        filtered = [o for o in objects if o["Key"].startswith(search)] if search else objects
        st.dataframe(
            [
                {
                    "Key": o["Key"],
                    "Size": fmt_size(o["Size"]),
                    "Last Modified": str(o.get("LastModified", ""))[:19],
                    "Storage Class": o.get("StorageClass", "STANDARD"),
                }
                for o in filtered
            ],
            use_container_width=True,
            hide_index=True,
        )
        if search and not filtered:
            st.info("No objects match that prefix.")
    else:
        st.info("Bucket is empty.")
