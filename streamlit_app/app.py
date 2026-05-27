import streamlit as st

st.set_page_config(
    page_title="MiniStack UI",
    page_icon="🗂️",
    layout="wide",
)

from pages.storage import s3, dynamo, rds, elasticache, ebs, efs, ecr, opensearch
from pages.compute import ec2, ecs, eks, lambda_, emr, batch, codebuild
from pages.networking import vpc, apigateway, apigatewayv2, alb, route53, cloudfront, waf
from pages.streaming import kinesis, firehose
from pages.messaging import sqs, sns, ses, eventbridge
from pages.orchestration import stepfunctions, mwaa
from pages.data import glue, athena, dynamostreams, rdsdata
from pages.security import iam, kms, sts, secretsmanager, cognito, acm
from pages.config_ops import ssm, appconfig, cloudformation, cloudtrail, autoscaling, backup
from pages.observability import cloudwatch, logs
from pages.other import appsync, transfer, iot, organizations

PAGES: dict[str, dict[str, object]] = {
    "Storage": {
        "S3": s3, "DynamoDB": dynamo, "RDS": rds, "ElastiCache": elasticache,
        "EBS": ebs, "EFS": efs, "ECR": ecr, "OpenSearch": opensearch,
    },
    "Compute": {
        "EC2": ec2, "ECS": ecs, "EKS": eks, "Lambda": lambda_,
        "EMR": emr, "Batch": batch, "CodeBuild": codebuild,
    },
    "Networking": {
        "VPC": vpc, "API Gateway": apigateway, "API Gateway v2": apigatewayv2,
        "ALB / ELBv2": alb, "Route 53": route53, "CloudFront": cloudfront, "WAF": waf,
    },
    "Streaming": {"Kinesis Data Stream": kinesis, "Kinesis Firehose": firehose},
    "Messaging": {"SQS": sqs, "SNS": sns, "SES": ses, "EventBridge": eventbridge},
    "Orchestration": {"Step Functions": stepfunctions, "MWAA": mwaa},
    "Data": {
        "Glue": glue, "Athena": athena,
        "DynamoDB Streams": dynamostreams, "RDS Data API": rdsdata,
    },
    "Security": {
        "IAM": iam, "KMS": kms, "STS": sts,
        "Secrets Manager": secretsmanager, "Cognito": cognito, "ACM": acm,
    },
    "Config / Ops": {
        "SSM Params": ssm, "AppConfig": appconfig, "CloudFormation": cloudformation,
        "CloudTrail": cloudtrail, "Auto Scaling": autoscaling, "Backup": backup,
    },
    "Observability": {"CloudWatch": cloudwatch, "Logs": logs},
    "Other": {"AppSync": appsync, "Transfer": transfer, "IoT Core": iot, "Organizations": organizations},
}


@st.cache_data(ttl=10, show_spinner=False)
def _check_ministack() -> bool:
    """Ping MiniStack — cached for 10 s to avoid blocking every rerun."""
    from aws_client import client
    try:
        client("s3").list_buckets()
        return True
    except Exception:
        return False


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🗂️ MiniStack")
    st.divider()

    search = st.text_input("🔍 Search services", placeholder="e.g. S3, Lambda…")

    if "page" not in st.session_state:
        st.session_state.page = "S3"

    for group, items in PAGES.items():
        filtered = {
            label: mod for label, mod in items.items()
            if not search or search.lower() in label.lower()
        }
        if not filtered:
            continue

        with st.expander(group, expanded=not search or any(
            search.lower() in lbl.lower() for lbl in items
        )):
            for label in filtered:
                if st.button(
                    label,
                    key=f"nav_{label}",
                    use_container_width=True,
                    type="primary" if st.session_state.page == label else "secondary",
                ):
                    st.session_state.page = label
                    st.rerun()

    st.divider()
    if _check_ministack():
        st.success("MiniStack online", icon="✅")
    else:
        st.error("MiniStack offline", icon="❌")

# ── Main area ─────────────────────────────────────────────────────────────────
current_label = st.session_state.page
for group, items in PAGES.items():
    if current_label in items:
        items[current_label].render()
        break
