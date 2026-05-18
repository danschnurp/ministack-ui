import streamlit as st

st.set_page_config(
    page_title="MiniStack UI",
    page_icon="🗂️",
    layout="wide",
)

import pages_s3 as s3_page
import pages_dynamo as dynamo_page
import pages_sqs as sqs_page
import pages_sns as sns_page
import pages_lambda as lambda_page
import pages_kinesis as kinesis_page
import pages_logs as logs_page
import pages_apigateway as apigw_page
from aws_client import client

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🗂️ MiniStack")
    st.divider()

    PAGES = {
        "Storage": {"S3": s3_page, "DynamoDB": dynamo_page},
        "Streaming": {"Kinesis": kinesis_page},
        "Messaging": {"SQS": sqs_page, "SNS": sns_page},
        "Compute": {"Lambda": lambda_page, "API Gateway": apigw_page},
        "Observability": {"Logs": logs_page},
    }

    if "page" not in st.session_state:
        st.session_state.page = "S3"

    for group, items in PAGES.items():
        st.markdown(f"<p style='font-size:11px;color:grey;font-weight:600;text-transform:uppercase'>{group}</p>",
                    unsafe_allow_html=True)
        for label in items:
            if st.button(label, use_container_width=True,
                         type="primary" if st.session_state.page == label else "secondary"):
                st.session_state.page = label

    # Status bar
    st.divider()
    try:
        boto_client = client("s3")
        boto_client.list_buckets()
        st.success("MiniStack online", icon="✅")
    except Exception:
        st.error("MiniStack offline", icon="❌")

# ── Main area ─────────────────────────────────────────────────────────────────
current_label = st.session_state.page
for group, items in PAGES.items():
    if current_label in items:
        items[current_label].render()
        break

