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
import pages_firehose as firehose_page
import pages_logs as logs_page
import pages_cloudwatch as cloudwatch_page
import pages_apigateway as apigw_page
import pages_ec2 as ec2_page
import pages_vpc as vpc_page
import pages_eventbridge as eventbridge_page
import pages_glue as glue_page
import pages_iam as iam_page
import pages_kms as kms_page
import pages_sts as sts_page
import pages_secretsmanager as secretsmanager_page
import pages_cognito as cognito_page
import pages_acm as acm_page
import pages_stepfunctions as stepfunctions_page
import pages_waf as waf_page
import pages_apigatewayv2 as apigwv2_page
import pages_alb as alb_page
import pages_route53 as route53_page
import pages_cloudfront as cloudfront_page
import pages_ecs as ecs_page
import pages_eks as eks_page
import pages_emr as emr_page
import pages_batch as batch_page
import pages_codebuild as codebuild_page
import pages_rds as rds_page
import pages_elasticache as elasticache_page
import pages_ebs as ebs_page
import pages_efs as efs_page
import pages_ecr as ecr_page
import pages_opensearch as opensearch_page
import pages_ses as ses_page
import pages_ssm as ssm_page
import pages_appconfig as appconfig_page
import pages_cloudformation as cloudformation_page
import pages_cloudtrail as cloudtrail_page
import pages_autoscaling as autoscaling_page
import pages_athena as athena_page
import pages_dynamostreams as dynamostreams_page
import pages_rdsdata as rdsdata_page
import pages_mwaa as mwaa_page
import pages_iot as iot_page
import pages_transfer as transfer_page
import pages_appsync as appsync_page
import pages_backup as backup_page
import pages_organizations as organizations_page
from aws_client import client

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🗂️ MiniStack")
    st.divider()

    PAGES = {
        "Storage": {"S3": s3_page, "DynamoDB": dynamo_page, "RDS": rds_page, "ElastiCache": elasticache_page, "EBS": ebs_page, "EFS": efs_page, "ECR": ecr_page, "OpenSearch": opensearch_page},
        "Compute": {"EC2": ec2_page, "ECS": ecs_page, "EKS": eks_page, "Lambda": lambda_page, "EMR": emr_page, "Batch": batch_page, "CodeBuild": codebuild_page},
        "Networking": {"VPC": vpc_page, "API Gateway": apigw_page, "API Gateway v2": apigwv2_page, "ALB / ELBv2": alb_page, "Route 53": route53_page, "CloudFront": cloudfront_page, "WAF": waf_page},
        "Streaming": {"Kinesis Data Stream": kinesis_page, "Kinesis Firehose": firehose_page},
        "Messaging": {"SQS": sqs_page, "SNS": sns_page, "SES": ses_page, "EventBridge": eventbridge_page},
        "Orchestration": {"Step Functions": stepfunctions_page, "MWAA": mwaa_page},
        "Data": {"Glue": glue_page, "Athena": athena_page, "DynamoDB Streams": dynamostreams_page, "RDS Data API": rdsdata_page},
        "Security": {"IAM": iam_page, "KMS": kms_page, "STS": sts_page, "Secrets Manager": secretsmanager_page, "Cognito": cognito_page, "ACM": acm_page},
        "Config / Ops": {"SSM Params": ssm_page, "AppConfig": appconfig_page, "CloudFormation": cloudformation_page, "CloudTrail": cloudtrail_page, "Auto Scaling": autoscaling_page, "Backup": backup_page},
        "Observability": {"CloudWatch": cloudwatch_page, "Logs": logs_page},
        "Other": {"AppSync": appsync_page, "Transfer": transfer_page, "IoT Core": iot_page, "Organizations": organizations_page},
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
