import streamlit as st
from aws_client import client


def fmt_size(b: int) -> str:
    if b >= 1_048_576:
        return f"{b / 1_048_576:.1f} MB"
    if b >= 1024:
        return f"{b // 1024} KB"
    return f"{b} B"


def render():
    st.subheader("S3")
    s3 = client("s3")

    try:
        buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not buckets:
        st.info("No buckets found.")
        return

    selected = st.selectbox("Bucket", buckets)

    if selected:
        try:
            objects = s3.list_objects_v2(Bucket=selected).get("Contents", [])
        except Exception as e:
            st.error(str(e))
            return

        st.caption(f"{len(objects)} objects")
        if objects:
            st.dataframe(
                [{"Key": o["Key"], "Size": fmt_size(o["Size"])} for o in objects],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Bucket is empty.")

