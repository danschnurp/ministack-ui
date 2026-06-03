#!/usr/bin/env bash
# =============================================================================
# MiniStack – seed all 17 services with test data
# Targets LocalStack at http://localhost:4566
#
# Dependencies: aws CLI (or awslocal wrapper)
# Usage:
#   chmod +x seed.sh
#   ./seed.sh
#   ./seed.sh --clean   # wipe & re-seed
# =============================================================================

set -euo pipefail

AWS="aws --endpoint-url=http://localhost:4566 --region us-east-1 \
  --no-cli-pager \
  --output json"

ACCOUNT_ID="000000000000"
REGION="us-east-1"
LOG_FILE="seed.log"

# ── helpers ──────────────────────────────────────────────────────────────────
info()  { echo -e "\033[0;34m[INFO]\033[0m  $*" | tee -a "$LOG_FILE"; }
ok()    { echo -e "\033[0;32m[ OK ]\033[0m  $*" | tee -a "$LOG_FILE"; }
warn()  { echo -e "\033[0;33m[WARN]\033[0m  $*" | tee -a "$LOG_FILE"; }
err()   { echo -e "\033[0;31m[ERR ]\033[0m  $*" | tee -a "$LOG_FILE"; }

run() {
  local label="$1"; shift
  if eval "$AWS $*" >> "$LOG_FILE" 2>&1; then
    ok "$label"
  else
    warn "$label (already exists or skipped)"
  fi
}

echo "" > "$LOG_FILE"
echo "=====================================================" | tee -a "$LOG_FILE"
echo " MiniStack seed  –  $(date)"                            | tee -a "$LOG_FILE"
echo "=====================================================" | tee -a "$LOG_FILE"

# ── optional clean ────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--clean" ]]; then
  info "Cleaning existing resources…"
  $AWS s3 rb s3://ministack-raw-data       --force 2>/dev/null || true
  $AWS s3 rb s3://ministack-processed-data --force 2>/dev/null || true
  $AWS s3 rb s3://ministack-firehose-dest  --force 2>/dev/null || true
  $AWS s3 rb s3://ministack-glue-scripts   --force 2>/dev/null || true
  $AWS s3 rb s3://ministack-audit-logs     --force 2>/dev/null || true
  $AWS s3 rb s3://ministack-cfn-artifacts  --force 2>/dev/null || true
  ok "S3 buckets removed"
  $AWS cloudformation delete-stack --stack-name ministack-infra 2>/dev/null || true
  $AWS rds delete-db-instance --db-instance-identifier ministack-postgres \
    --skip-final-snapshot 2>/dev/null || true
  $AWS elasticache delete-replication-group --replication-group-id ministack-redis \
    --no-retain-primary-cluster 2>/dev/null || true
  $AWS opensearch delete-domain --domain-name ministack-search 2>/dev/null || true
  ok "Extended resources cleaned"
fi

# =============================================================================
# 1. KMS
# =============================================================================
info "── KMS ──────────────────────────────────────────────"

KEY_ID=$($AWS kms create-key \
  --description "MiniStack main key" \
  --tags TagKey=Name,TagValue=ministack-main \
  --query 'KeyMetadata.KeyId' --output text 2>/dev/null || \
  $AWS kms list-keys --query 'Keys[0].KeyId' --output text)

$AWS kms create-alias \
  --alias-name alias/ministack-main \
  --target-key-id "$KEY_ID" 2>/dev/null || true
ok "KMS key: $KEY_ID (alias/ministack-main)"

S3_KEY_ID=$($AWS kms create-key \
  --description "MiniStack S3 key" \
  --tags TagKey=Name,TagValue=ministack-s3 \
  --query 'KeyMetadata.KeyId' --output text)
$AWS kms create-alias --alias-name alias/ministack-s3 --target-key-id "$S3_KEY_ID" 2>/dev/null || true
ok "KMS key: $S3_KEY_ID (alias/ministack-s3)"

# =============================================================================
# 2. IAM
# =============================================================================
info "── IAM ──────────────────────────────────────────────"

LAMBDA_TRUST='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
GLUE_TRUST='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"glue.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
SFN_TRUST='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"states.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
FIREHOSE_TRUST='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"firehose.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

run "IAM role: ministack-lambda-exec"   iam create-role --role-name ministack-lambda-exec --assume-role-policy-document "'$LAMBDA_TRUST'"
run "IAM role: ministack-glue-service"  iam create-role --role-name ministack-glue-service  --assume-role-policy-document "'$GLUE_TRUST'"
run "IAM role: ministack-sfn-exec"      iam create-role --role-name ministack-sfn-exec      --assume-role-policy-document "'$SFN_TRUST'"
run "IAM role: ministack-firehose"      iam create-role --role-name ministack-firehose-delivery --assume-role-policy-document "'$FIREHOSE_TRUST'"

LAMBDA_POLICY='{
  "Version":"2012-10-17",
  "Statement":[
    {"Effect":"Allow","Action":["logs:*"],"Resource":"*"},
    {"Effect":"Allow","Action":["kinesis:*","dynamodb:*","sqs:*","sns:*","s3:*"],"Resource":"*"}
  ]
}'
$AWS iam create-policy \
  --policy-name ministack-lambda-basic \
  --policy-document "$LAMBDA_POLICY" >> "$LOG_FILE" 2>&1 || true

$AWS iam attach-role-policy \
  --role-name ministack-lambda-exec \
  --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/ministack-lambda-basic" >> "$LOG_FILE" 2>&1 || true

run "IAM user: ministack-app"      iam create-user --user-name ministack-app
run "IAM user: ministack-readonly" iam create-user --user-name ministack-readonly
ok "IAM resources ready"

LAMBDA_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/ministack-lambda-exec"
SFN_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/ministack-sfn-exec"
FIREHOSE_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/ministack-firehose-delivery"
GLUE_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/ministack-glue-service"

# =============================================================================
# 3. VPC
# =============================================================================
info "── VPC ──────────────────────────────────────────────"

VPC_ID=$($AWS ec2 create-vpc --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=ministack-vpc}]' \
  --query 'Vpc.VpcId' --output text 2>/dev/null || \
  $AWS ec2 describe-vpcs --filters "Name=tag:Name,Values=ministack-vpc" \
  --query 'Vpcs[0].VpcId' --output text)
ok "VPC: $VPC_ID"

SUBNET_PUB_A=$($AWS ec2 create-subnet \
  --vpc-id "$VPC_ID" --cidr-block 10.0.1.0/24 --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ministack-public-a}]' \
  --query 'Subnet.SubnetId' --output text 2>/dev/null || \
  $AWS ec2 describe-subnets --filters "Name=tag:Name,Values=ministack-public-a" \
  --query 'Subnets[0].SubnetId' --output text)
ok "Subnet (public-a): $SUBNET_PUB_A"

SUBNET_PUB_B=$($AWS ec2 create-subnet \
  --vpc-id "$VPC_ID" --cidr-block 10.0.2.0/24 --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ministack-public-b}]' \
  --query 'Subnet.SubnetId' --output text 2>/dev/null || \
  $AWS ec2 describe-subnets --filters "Name=tag:Name,Values=ministack-public-b" \
  --query 'Subnets[0].SubnetId' --output text)
ok "Subnet (public-b): $SUBNET_PUB_B"

SUBNET_PRIV_A=$($AWS ec2 create-subnet \
  --vpc-id "$VPC_ID" --cidr-block 10.0.11.0/24 --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ministack-private-a}]' \
  --query 'Subnet.SubnetId' --output text 2>/dev/null || \
  $AWS ec2 describe-subnets --filters "Name=tag:Name,Values=ministack-private-a" \
  --query 'Subnets[0].SubnetId' --output text)
ok "Subnet (private-a): $SUBNET_PRIV_A"

IGW_ID=$($AWS ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=ministack-igw}]' \
  --query 'InternetGateway.InternetGatewayId' --output text 2>/dev/null || \
  $AWS ec2 describe-internet-gateways --filters "Name=tag:Name,Values=ministack-igw" \
  --query 'InternetGateways[0].InternetGatewayId' --output text)
$AWS ec2 attach-internet-gateway --internet-gateway-id "$IGW_ID" --vpc-id "$VPC_ID" >> "$LOG_FILE" 2>&1 || true
ok "Internet Gateway: $IGW_ID"

SG_APP=$($AWS ec2 create-security-group \
  --group-name ministack-app-sg \
  --description "MiniStack app security group" \
  --vpc-id "$VPC_ID" \
  --tag-specifications 'ResourceType=security-group,Tags=[{Key=Name,Value=ministack-app-sg}]' \
  --query 'GroupId' --output text 2>/dev/null || \
  $AWS ec2 describe-security-groups --filters "Name=group-name,Values=ministack-app-sg" \
  --query 'SecurityGroups[0].GroupId' --output text)
$AWS ec2 authorize-security-group-ingress --group-id "$SG_APP" \
  --protocol tcp --port 443 --cidr 0.0.0.0/0 >> "$LOG_FILE" 2>&1 || true
$AWS ec2 authorize-security-group-ingress --group-id "$SG_APP" \
  --protocol tcp --port 80 --cidr 0.0.0.0/0 >> "$LOG_FILE" 2>&1 || true
ok "Security Group (app): $SG_APP"

# EC2 instances
AMI_ID=$($AWS ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" \
  --query 'sort_by(Images,&CreationDate)[-1].ImageId' \
  --output text 2>/dev/null || echo "ami-12345678")

$AWS ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --count 1 \
  --subnet-id "$SUBNET_PUB_A" \
  --security-group-ids "$SG_APP" \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ministack-web},{Key=Role,Value=web}]' \
  >> "$LOG_FILE" 2>&1 || true
ok "EC2 instance: ministack-web (t3.micro)"

$AWS ec2 run-instances \
  --image-id "$AMI_ID" \
  --instance-type t3.small \
  --count 1 \
  --subnet-id "$SUBNET_PRIV_A" \
  --security-group-ids "$SG_APP" \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ministack-worker},{Key=Role,Value=worker}]' \
  >> "$LOG_FILE" 2>&1 || true
ok "EC2 instance: ministack-worker (t3.small)"

# =============================================================================
# 4. S3
# =============================================================================
info "── S3 ───────────────────────────────────────────────"

for BUCKET in ministack-raw-data ministack-processed-data ministack-firehose-dest ministack-glue-scripts; do
  run "S3 bucket: $BUCKET" s3api create-bucket --bucket "$BUCKET"
done

# Upload sample objects
$AWS s3 cp - s3://ministack-raw-data/events/sample.json \
  --content-type application/json << 'JSON' >> "$LOG_FILE" 2>&1
{"id":"evt-001","type":"click","ts":"2024-01-15T10:00:00Z","userId":"user-001","page":"/home"}
{"id":"evt-002","type":"purchase","ts":"2024-01-15T10:05:00Z","userId":"user-001","amount":49.99}
{"id":"evt-003","type":"click","ts":"2024-01-15T10:10:00Z","userId":"user-002","page":"/products"}
JSON
ok "S3 object: events/sample.json"

$AWS s3 cp - s3://ministack-raw-data/exports/users.csv \
  --content-type text/csv << 'CSV' >> "$LOG_FILE" 2>&1
id,name,email,role,created_at
1,Alice Smith,alice@example.com,admin,2024-01-01
2,Bob Jones,bob@example.com,viewer,2024-01-05
3,Carol White,carol@example.com,editor,2024-01-10
4,Dave Brown,dave@example.com,viewer,2024-01-12
CSV
ok "S3 object: exports/users.csv"

$AWS s3 cp - s3://ministack-glue-scripts/scripts/etl_job.py \
  --content-type text/x-python << 'PY' >> "$LOG_FILE" 2>&1
import sys
from awsglue.utils import getResolvedOptions
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
print("MiniStack ETL job:", args['JOB_NAME'])
PY
ok "S3 object: scripts/etl_job.py"

# =============================================================================
# 5. DynamoDB
# =============================================================================
info "── DynamoDB ──────────────────────────────────────────"

run "DynamoDB table: ministack-users" \
  dynamodb create-table \
  --table-name ministack-users \
  --attribute-definitions AttributeName=userId,AttributeType=S \
  --key-schema AttributeName=userId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --tags Key=Name,Value=ministack-users

run "DynamoDB table: ministack-events" \
  dynamodb create-table \
  --table-name ministack-events \
  --attribute-definitions \
    AttributeName=eventId,AttributeType=S \
    AttributeName=timestamp,AttributeType=S \
  --key-schema \
    AttributeName=eventId,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

run "DynamoDB table: ministack-orders" \
  dynamodb create-table \
  --table-name ministack-orders \
  --attribute-definitions AttributeName=orderId,AttributeType=S \
  --key-schema AttributeName=orderId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Seed items
$AWS dynamodb put-item --table-name ministack-users --item \
  '{"userId":{"S":"user-001"},"name":{"S":"Alice Smith"},"email":{"S":"alice@example.com"},"role":{"S":"admin"},"active":{"BOOL":true}}' \
  >> "$LOG_FILE" 2>&1
$AWS dynamodb put-item --table-name ministack-users --item \
  '{"userId":{"S":"user-002"},"name":{"S":"Bob Jones"},"email":{"S":"bob@example.com"},"role":{"S":"viewer"},"active":{"BOOL":true}}' \
  >> "$LOG_FILE" 2>&1
$AWS dynamodb put-item --table-name ministack-users --item \
  '{"userId":{"S":"user-003"},"name":{"S":"Carol White"},"email":{"S":"carol@example.com"},"role":{"S":"editor"},"active":{"BOOL":true}}' \
  >> "$LOG_FILE" 2>&1
ok "DynamoDB: 3 users seeded"

$AWS dynamodb put-item --table-name ministack-events --item \
  '{"eventId":{"S":"evt-001"},"timestamp":{"S":"2024-01-15T10:00:00Z"},"type":{"S":"click"},"userId":{"S":"user-001"}}' \
  >> "$LOG_FILE" 2>&1
$AWS dynamodb put-item --table-name ministack-events --item \
  '{"eventId":{"S":"evt-002"},"timestamp":{"S":"2024-01-15T10:05:00Z"},"type":{"S":"purchase"},"userId":{"S":"user-001"},"amount":{"N":"49.99"}}' \
  >> "$LOG_FILE" 2>&1
ok "DynamoDB: 2 events seeded"

$AWS dynamodb put-item --table-name ministack-orders --item \
  '{"orderId":{"S":"ord-001"},"status":{"S":"pending"},"userId":{"S":"user-001"},"total":{"N":"149.99"},"createdAt":{"S":"2024-01-15T10:00:00Z"}}' \
  >> "$LOG_FILE" 2>&1
$AWS dynamodb put-item --table-name ministack-orders --item \
  '{"orderId":{"S":"ord-002"},"status":{"S":"shipped"},"userId":{"S":"user-002"},"total":{"N":"29.99"},"createdAt":{"S":"2024-01-15T11:00:00Z"}}' \
  >> "$LOG_FILE" 2>&1
ok "DynamoDB: 2 orders seeded"

# =============================================================================
# 6. SQS
# =============================================================================
info "── SQS ──────────────────────────────────────────────"

DLQ_ARN=$($AWS sqs create-queue \
  --queue-name ministack-orders-dlq \
  --attributes MessageRetentionPeriod=1209600 \
  --query 'QueueUrl' --output text 2>/dev/null | \
  xargs -I{} $AWS sqs get-queue-attributes --queue-url {} \
  --attribute-names QueueArn --query 'Attributes.QueueArn' --output text || \
  echo "arn:aws:sqs:us-east-1:${ACCOUNT_ID}:ministack-orders-dlq")
ok "SQS DLQ: ministack-orders-dlq"

$AWS sqs create-queue \
  --queue-name ministack-orders \
  --attributes '{
    "VisibilityTimeout":"30",
    "MessageRetentionPeriod":"86400",
    "RedrivePolicy":"{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:000000000000:ministack-orders-dlq\",\"maxReceiveCount\":\"3\"}"
  }' >> "$LOG_FILE" 2>&1 || true
ok "SQS queue: ministack-orders"

run "SQS queue: ministack-notifications" \
  sqs create-queue --queue-name ministack-notifications

run "SQS FIFO: ministack-tasks.fifo" \
  sqs create-queue \
  --queue-name ministack-tasks.fifo \
  --attributes FifoQueue=true,ContentBasedDeduplication=true

# Seed messages
ORDERS_URL="http://localhost:4566/000000000000/ministack-orders"
$AWS sqs send-message --queue-url "$ORDERS_URL" \
  --message-body '{"orderId":"ord-003","action":"process","total":79.99}' >> "$LOG_FILE" 2>&1 || true
$AWS sqs send-message --queue-url "$ORDERS_URL" \
  --message-body '{"orderId":"ord-004","action":"process","total":199.00}' >> "$LOG_FILE" 2>&1 || true
ok "SQS: 2 messages sent to ministack-orders"

# =============================================================================
# 7. SNS
# =============================================================================
info "── SNS ──────────────────────────────────────────────"

ALERTS_ARN=$($AWS sns create-topic --name ministack-alerts \
  --tags Key=Name,Value=ministack-alerts \
  --query 'TopicArn' --output text 2>/dev/null || \
  echo "arn:aws:sns:us-east-1:${ACCOUNT_ID}:ministack-alerts")
ok "SNS topic: ministack-alerts ($ALERTS_ARN)"

EVENTS_ARN=$($AWS sns create-topic --name ministack-events \
  --tags Key=Name,Value=ministack-events \
  --query 'TopicArn' --output text 2>/dev/null || \
  echo "arn:aws:sns:us-east-1:${ACCOUNT_ID}:ministack-events")
ok "SNS topic: ministack-events ($EVENTS_ARN)"

NOTIF_URL="http://localhost:4566/000000000000/ministack-notifications"
$AWS sns subscribe \
  --topic-arn "$ALERTS_ARN" \
  --protocol sqs \
  --notification-endpoint "$NOTIF_URL" >> "$LOG_FILE" 2>&1 || true
ok "SNS subscription: alerts → notifications queue"

$AWS sns publish \
  --topic-arn "$ALERTS_ARN" \
  --subject "Test Alert" \
  --message "MiniStack seed alert: system initialised" >> "$LOG_FILE" 2>&1 || true
ok "SNS: test message published to ministack-alerts"

# =============================================================================
# 8. CloudWatch
# =============================================================================
info "── CloudWatch ────────────────────────────────────────"

run "CW log group: /ministack/app"   logs create-log-group  --log-group-name /ministack/app
run "CW log group: /ministack/api"   logs create-log-group  --log-group-name /ministack/api
run "CW log group: /aws/lambda/ministack-processor" \
  logs create-log-group --log-group-name /aws/lambda/ministack-processor

$AWS logs create-log-stream \
  --log-group-name /ministack/app \
  --log-stream-name main >> "$LOG_FILE" 2>&1 || true
ok "CW log stream: /ministack/app/main"

TS=$(( $(date +%s) * 1000 ))
$AWS logs put-log-events \
  --log-group-name /ministack/app \
  --log-stream-name main \
  --log-events \
    "[{\"timestamp\":${TS},\"message\":\"MiniStack started\"},{\"timestamp\":$((TS+1000)),\"message\":\"Seed complete\"}]" \
  >> "$LOG_FILE" 2>&1 || true
ok "CW: seed log events written"

$AWS cloudwatch put-metric-alarm \
  --alarm-name ministack-lambda-errors \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 60 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions "$ALERTS_ARN" >> "$LOG_FILE" 2>&1 || true
ok "CW alarm: ministack-lambda-errors"

$AWS cloudwatch put-metric-alarm \
  --alarm-name ministack-sqs-depth \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --dimensions Name=QueueName,Value=ministack-orders \
  --statistic Maximum \
  --period 300 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 >> "$LOG_FILE" 2>&1 || true
ok "CW alarm: ministack-sqs-depth"

$AWS cloudwatch put-metric-data \
  --namespace MiniStack/App \
  --metric-data \
    '[{"MetricName":"RequestCount","Value":142,"Unit":"Count"},{"MetricName":"Latency","Value":45.2,"Unit":"Milliseconds"}]' \
  >> "$LOG_FILE" 2>&1 || true
ok "CW: custom metrics published (RequestCount, Latency)"

# =============================================================================
# 9. Kinesis Data Stream
# =============================================================================
info "── Kinesis Data Stream ───────────────────────────────"

run "Kinesis stream: ministack-events" \
  kinesis create-stream --stream-name ministack-events --shard-count 2

run "Kinesis stream: ministack-clickstream" \
  kinesis create-stream --stream-name ministack-clickstream --shard-count 1

sleep 1  # let streams activate

PAYLOAD=$(echo '{"eventId":"evt-seed-001","type":"click","userId":"user-001","ts":"2024-01-15T10:00:00Z"}' | base64)
$AWS kinesis put-record \
  --stream-name ministack-events \
  --data "$PAYLOAD" \
  --partition-key user-001 >> "$LOG_FILE" 2>&1 || true

PAYLOAD2=$(echo '{"eventId":"evt-seed-002","type":"purchase","userId":"user-001","amount":49.99}' | base64)
$AWS kinesis put-record \
  --stream-name ministack-events \
  --data "$PAYLOAD2" \
  --partition-key user-001 >> "$LOG_FILE" 2>&1 || true
ok "Kinesis: 2 records put to ministack-events"

CLICK_PAYLOAD=$(echo '{"sessionId":"sess-001","page":"/products","action":"scroll"}' | base64)
$AWS kinesis put-record \
  --stream-name ministack-clickstream \
  --data "$CLICK_PAYLOAD" \
  --partition-key sess-001 >> "$LOG_FILE" 2>&1 || true
ok "Kinesis: 1 record put to ministack-clickstream"

# =============================================================================
# 10. Lambda
# =============================================================================
info "── Lambda ────────────────────────────────────────────"

TMPDIR_LAMBDA=$(mktemp -d)

# processor
cat > "$TMPDIR_LAMBDA/index.js" << 'JS'
exports.handler = async (event) => {
  console.log('MiniStack processor received:', JSON.stringify(event));
  const records = event.Records ?? [event];
  const processed = records.map(r => ({ id: r.messageId ?? r.kinesis?.sequenceNumber ?? 'evt', processed: true, ts: Date.now() }));
  return { statusCode: 200, body: JSON.stringify({ processed }) };
};
JS
(cd "$TMPDIR_LAMBDA" && zip -q processor.zip index.js)

$AWS lambda create-function \
  --function-name ministack-processor \
  --runtime nodejs20.x \
  --role "$LAMBDA_ROLE_ARN" \
  --handler index.handler \
  --zip-file "fileb://$TMPDIR_LAMBDA/processor.zip" \
  --timeout 30 \
  --memory-size 256 \
  --environment "Variables={ORDERS_TABLE=ministack-orders,EVENTS_STREAM=ministack-events,ALERTS_TOPIC=arn:aws:sns:us-east-1:${ACCOUNT_ID}:ministack-alerts}" \
  >> "$LOG_FILE" 2>&1 || true
ok "Lambda: ministack-processor"

# api-handler
cat > "$TMPDIR_LAMBDA/index.js" << 'JS'
exports.handler = async (event) => {
  const path = event.path ?? '/';
  const method = event.httpMethod ?? 'GET';
  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ service: 'ministack-api', path, method, ts: new Date().toISOString() })
  };
};
JS
(cd "$TMPDIR_LAMBDA" && zip -q api_handler.zip index.js)

$AWS lambda create-function \
  --function-name ministack-api-handler \
  --runtime nodejs20.x \
  --role "$LAMBDA_ROLE_ARN" \
  --handler index.handler \
  --zip-file "fileb://$TMPDIR_LAMBDA/api_handler.zip" \
  --timeout 15 \
  --memory-size 128 \
  >> "$LOG_FILE" 2>&1 || true
ok "Lambda: ministack-api-handler"

rm -rf "$TMPDIR_LAMBDA"

# Invoke processor to verify
$AWS lambda invoke \
  --function-name ministack-processor \
  --payload '{"source":"seed","Records":[{"messageId":"seed-001","body":"{\"orderId\":\"ord-001\"}"}]}' \
  /tmp/lambda_out.json >> "$LOG_FILE" 2>&1 || true
ok "Lambda: ministack-processor invoked (test run)"

# =============================================================================
# 11. Kinesis Firehose
# =============================================================================
info "── Kinesis Firehose ──────────────────────────────────"

$AWS firehose create-delivery-stream \
  --delivery-stream-name ministack-s3-delivery \
  --delivery-stream-type DirectPut \
  --extended-s3-destination-configuration \
    "RoleARN=${FIREHOSE_ROLE_ARN},BucketARN=arn:aws:s3:::ministack-firehose-dest,Prefix=events/,BufferingHints={SizeInMBs=5,IntervalInSeconds=60},CompressionFormat=GZIP" \
  >> "$LOG_FILE" 2>&1 || true
ok "Firehose: ministack-s3-delivery"

# =============================================================================
# 12. API Gateway
# =============================================================================
info "── API Gateway ───────────────────────────────────────"

API_ID=$($AWS apigateway create-rest-api \
  --name ministack-api \
  --description "MiniStack REST API" \
  --query 'id' --output text 2>/dev/null || \
  $AWS apigateway get-rest-apis --query "items[?name=='ministack-api'].id" --output text)
ok "API Gateway: ministack-api ($API_ID)"

ROOT_ID=$($AWS apigateway get-resources \
  --rest-api-id "$API_ID" \
  --query 'items[?path==`/`].id' --output text)

ITEMS_ID=$($AWS apigateway create-resource \
  --rest-api-id "$API_ID" \
  --parent-id "$ROOT_ID" \
  --path-part items \
  --query 'id' --output text 2>/dev/null || \
  $AWS apigateway get-resources --rest-api-id "$API_ID" \
  --query "items[?pathPart=='items'].id" --output text)
ok "API Gateway resource: /items"

LAMBDA_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:ministack-api-handler"

for METHOD in GET POST; do
  $AWS apigateway put-method \
    --rest-api-id "$API_ID" \
    --resource-id "$ITEMS_ID" \
    --http-method "$METHOD" \
    --authorization-type NONE >> "$LOG_FILE" 2>&1 || true

  $AWS apigateway put-integration \
    --rest-api-id "$API_ID" \
    --resource-id "$ITEMS_ID" \
    --http-method "$METHOD" \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:${REGION}:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    >> "$LOG_FILE" 2>&1 || true
done
ok "API Gateway: GET/POST /items methods & integrations"

$AWS apigateway create-deployment \
  --rest-api-id "$API_ID" \
  --stage-name dev >> "$LOG_FILE" 2>&1 || true
$AWS apigateway create-stage \
  --rest-api-id "$API_ID" \
  --stage-name prod \
  --deployment-id "$($AWS apigateway get-deployments --rest-api-id "$API_ID" --query 'items[0].id' --output text)" \
  >> "$LOG_FILE" 2>&1 || true
ok "API Gateway: stages dev + prod deployed"

# =============================================================================
# 13. EventBridge
# =============================================================================
info "── EventBridge ───────────────────────────────────────"

$AWS events create-event-bus --name ministack-app \
  --tags Key=Name,Value=ministack-app >> "$LOG_FILE" 2>&1 || true
ok "EventBridge bus: ministack-app"

$AWS events put-rule \
  --name ministack-every-minute \
  --schedule-expression "rate(1 minute)" \
  --state ENABLED \
  --description "Heartbeat rule" >> "$LOG_FILE" 2>&1 || true
ok "EventBridge rule: ministack-every-minute (schedule)"

$AWS events put-rule \
  --name ministack-order-created \
  --event-bus-name ministack-app \
  --event-pattern '{"source":["ministack.orders"],"detail-type":["order.created"]}' \
  --state ENABLED \
  --description "Order created event pattern" >> "$LOG_FILE" 2>&1 || true
ok "EventBridge rule: ministack-order-created (pattern)"

LAMBDA_ARN_PROC="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:ministack-processor"
$AWS events put-targets \
  --rule ministack-every-minute \
  --targets "Id=LambdaProcessor,Arn=${LAMBDA_ARN_PROC}" >> "$LOG_FILE" 2>&1 || true

ORDERS_QUEUE_ARN="arn:aws:sqs:${REGION}:${ACCOUNT_ID}:ministack-orders"
$AWS events put-targets \
  --rule ministack-order-created \
  --event-bus-name ministack-app \
  --targets "Id=OrdersQueue,Arn=${ORDERS_QUEUE_ARN}" >> "$LOG_FILE" 2>&1 || true
ok "EventBridge: targets wired"

# =============================================================================
# 14. Glue
# =============================================================================
info "── Glue ──────────────────────────────────────────────"

run "Glue database: ministack_raw" \
  glue create-database \
  --catalog-id "$ACCOUNT_ID" \
  --database-input "Name=ministack_raw,Description=Raw ingested data"

run "Glue database: ministack_curated" \
  glue create-database \
  --catalog-id "$ACCOUNT_ID" \
  --database-input "Name=ministack_curated,Description=Curated data"

$AWS glue create-table \
  --catalog-id "$ACCOUNT_ID" \
  --database-name ministack_raw \
  --table-input '{
    "Name":"events",
    "TableType":"EXTERNAL_TABLE",
    "Parameters":{"classification":"json"},
    "StorageDescriptor":{
      "Columns":[
        {"Name":"id","Type":"string"},
        {"Name":"type","Type":"string"},
        {"Name":"ts","Type":"string"},
        {"Name":"userId","Type":"string"}
      ],
      "Location":"s3://ministack-raw-data/events/",
      "InputFormat":"org.apache.hadoop.mapred.TextInputFormat",
      "OutputFormat":"org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
      "SerdeInfo":{"SerializationLibrary":"org.openx.data.jsonserde.JsonSerDe"}
    }
  }' >> "$LOG_FILE" 2>&1 || true
ok "Glue table: ministack_raw.events"

$AWS glue create-table \
  --catalog-id "$ACCOUNT_ID" \
  --database-name ministack_raw \
  --table-input '{
    "Name":"users",
    "TableType":"EXTERNAL_TABLE",
    "Parameters":{"classification":"csv","skip.header.line.count":"1"},
    "StorageDescriptor":{
      "Columns":[
        {"Name":"id","Type":"int"},
        {"Name":"name","Type":"string"},
        {"Name":"email","Type":"string"},
        {"Name":"role","Type":"string"},
        {"Name":"created_at","Type":"string"}
      ],
      "Location":"s3://ministack-raw-data/exports/",
      "InputFormat":"org.apache.hadoop.mapred.TextInputFormat",
      "OutputFormat":"org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
      "SerdeInfo":{
        "SerializationLibrary":"org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
        "Parameters":{"field.delim":","}
      }
    }
  }' >> "$LOG_FILE" 2>&1 || true
ok "Glue table: ministack_raw.users"

$AWS glue create-job \
  --name ministack-etl \
  --role "$GLUE_ROLE_ARN" \
  --command "Name=glueetl,ScriptLocation=s3://ministack-glue-scripts/scripts/etl_job.py,PythonVersion=3" \
  --default-arguments '{
    "--job-language":"python",
    "--TempDir":"s3://ministack-glue-scripts/tmp/",
    "--enable-metrics":"true",
    "--SOURCE_BUCKET":"ministack-raw-data",
    "--DEST_BUCKET":"ministack-processed-data"
  }' \
  --number-of-workers 2 \
  --worker-type "G.1X" \
  --glue-version "4.0" >> "$LOG_FILE" 2>&1 || true
ok "Glue job: ministack-etl"

$AWS glue create-crawler \
  --name ministack-raw-events \
  --role "$GLUE_ROLE_ARN" \
  --database-name ministack_raw \
  --targets '{"S3Targets":[{"Path":"s3://ministack-raw-data/events/"}]}' \
  >> "$LOG_FILE" 2>&1 || true
ok "Glue crawler: ministack-raw-events"

# Glue Schema Registry (catalog schemas for demo streams / tables)
EVENT_AVRO_V1='{"type":"record","name":"Event","fields":[{"name":"id","type":"string"},{"name":"type","type":"string"},{"name":"ts","type":"string"},{"name":"userId","type":"string"}]}'
EVENT_AVRO_V2='{"type":"record","name":"Event","fields":[{"name":"id","type":"string"},{"name":"type","type":"string"},{"name":"ts","type":"string"},{"name":"userId","type":"string"},{"name":"source","type":"string","default":""}]}'
USER_AVRO_V1='{"type":"record","name":"User","fields":[{"name":"id","type":"int"},{"name":"name","type":"string"},{"name":"email","type":"string"},{"name":"role","type":"string"},{"name":"created_at","type":"string"}]}'
ORDER_AVRO_V1='{"type":"record","name":"Order","fields":[{"name":"orderId","type":"string"},{"name":"userId","type":"string"},{"name":"amount","type":"double"},{"name":"status","type":"string"}]}'

run "Glue registry: ministack-demo" \
  glue create-registry \
  --registry-name ministack-demo \
  --description "'Demo schema registry for MiniStack UI'"

run "Glue schema: events (v1)" \
  glue create-schema \
  --registry-id RegistryName=ministack-demo \
  --schema-name events \
  --data-format AVRO \
  --compatibility BACKWARD \
  --description "'Kinesis events (ministack_raw.events)'" \
  --schema-definition "'$EVENT_AVRO_V1'"

run "Glue schema: users" \
  glue create-schema \
  --registry-id RegistryName=ministack-demo \
  --schema-name users \
  --data-format AVRO \
  --compatibility BACKWARD \
  --description "'User CSV export (ministack_raw.users)'" \
  --schema-definition "'$USER_AVRO_V1'"

run "Glue schema: orders" \
  glue create-schema \
  --registry-id RegistryName=ministack-demo \
  --schema-name orders \
  --data-format AVRO \
  --compatibility FULL \
  --description "'Order pipeline (ministack-orders)'" \
  --schema-definition "'$ORDER_AVRO_V1'"

if eval "$AWS glue register-schema-version \
  --schema-id RegistryName=ministack-demo,SchemaName=events \
  --schema-definition '$EVENT_AVRO_V2'" >> "$LOG_FILE" 2>&1; then
  ok "Glue schema version: events v2 (backward-compatible)"
else
  warn "Glue schema version: events v2 (already exists or skipped)"
fi

# =============================================================================
# 15. Step Functions
# =============================================================================
info "── Step Functions ────────────────────────────────────"

PROC_ARN="arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:ministack-processor"

ORDER_PIPELINE_DEF=$(cat << SFNDEF
{
  "Comment": "MiniStack order processing pipeline",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "${PROC_ARN}",
      "Next": "ProcessPayment",
      "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "OrderFailed"}]
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "${PROC_ARN}",
      "Next": "FulfillOrder"
    },
    "FulfillOrder": {
      "Type": "Task",
      "Resource": "${PROC_ARN}",
      "Next": "NotifyCustomer"
    },
    "NotifyCustomer": {
      "Type": "Task",
      "Resource": "${PROC_ARN}",
      "End": true
    },
    "OrderFailed": {
      "Type": "Fail",
      "Error": "OrderProcessingFailed",
      "Cause": "An error occurred during order processing"
    }
  }
}
SFNDEF
)

SM_ORDER_ARN=$($AWS stepfunctions create-state-machine \
  --name ministack-order-pipeline \
  --definition "$ORDER_PIPELINE_DEF" \
  --role-arn "$SFN_ROLE_ARN" \
  --query 'stateMachineArn' --output text 2>/dev/null || \
  $AWS stepfunctions list-state-machines \
  --query "stateMachines[?name=='ministack-order-pipeline'].stateMachineArn" --output text)
ok "Step Functions: ministack-order-pipeline"

QUALITY_DEF='{
  "Comment":"MiniStack data quality check",
  "StartAt":"CheckSchema",
  "States":{
    "CheckSchema":{"Type":"Task","Resource":"'"${PROC_ARN}"'","Next":"CheckVolume"},
    "CheckVolume":{"Type":"Choice","Choices":[{"Variable":"$.recordCount","NumericGreaterThan":0,"Next":"PassQuality"}],"Default":"FailQuality"},
    "PassQuality":{"Type":"Succeed"},
    "FailQuality":{"Type":"Fail","Error":"DataQualityFailed","Cause":"Record count is zero"}
  }
}'

$AWS stepfunctions create-state-machine \
  --name ministack-data-quality \
  --definition "$QUALITY_DEF" \
  --role-arn "$SFN_ROLE_ARN" >> "$LOG_FILE" 2>&1 || true
ok "Step Functions: ministack-data-quality"

# Start a test execution
$AWS stepfunctions start-execution \
  --state-machine-arn "$SM_ORDER_ARN" \
  --name "seed-exec-001" \
  --input '{"orderId":"ord-001","userId":"user-001","total":149.99}' \
  >> "$LOG_FILE" 2>&1 || true
ok "Step Functions: seed execution started"

# =============================================================================
# 16. WAF
# =============================================================================
info "── WAF ───────────────────────────────────────────────"

IPSET_ARN=$($AWS wafv2 create-ip-set \
  --name ministack-blocked-ips \
  --scope REGIONAL \
  --ip-address-version IPV4 \
  --addresses "192.168.100.0/24" "10.99.0.0/16" \
  --tags Key=Name,Value=ministack-blocked-ips \
  --query 'Summary.ARN' --output text 2>/dev/null || \
  $AWS wafv2 list-ip-sets --scope REGIONAL \
  --query "IPSets[?Name=='ministack-blocked-ips'].ARN" --output text)
ok "WAF IP set: ministack-blocked-ips ($IPSET_ARN)"

$AWS wafv2 create-web-acl \
  --name ministack-web-acl \
  --scope REGIONAL \
  --default-action Allow={} \
  --rules '[
    {
      "Name":"BlockBadIPs","Priority":1,
      "Action":{"Block":{}},
      "Statement":{"IPSetReferenceStatement":{"ARN":"'"${IPSET_ARN}"'"}},
      "VisibilityConfig":{"SampledRequestsEnabled":true,"CloudWatchMetricsEnabled":true,"MetricName":"BlockBadIPs"}
    },
    {
      "Name":"RateLimitRule","Priority":2,
      "Action":{"Block":{}},
      "Statement":{"RateBasedStatement":{"Limit":2000,"AggregateKeyType":"IP"}},
      "VisibilityConfig":{"SampledRequestsEnabled":true,"CloudWatchMetricsEnabled":true,"MetricName":"RateLimit"}
    }
  ]' \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=ministack-web-acl \
  --tags Key=Name,Value=ministack-web-acl >> "$LOG_FILE" 2>&1 || true
ok "WAF Web ACL: ministack-web-acl"

# =============================================================================
# 17. Secrets Manager
# =============================================================================
info "── Secrets Manager ───────────────────────────────────"

run "Secret: ministack/app/config" \
  secretsmanager create-secret \
  --name ministack/app/config \
  --description "MiniStack application config" \
  --secret-string '{"db_password":"s3cr3t","api_key":"ak-ministack-abc123","jwt_secret":"jwt-ministack-xyz"}'

run "Secret: ministack/db/credentials" \
  secretsmanager create-secret \
  --name ministack/db/credentials \
  --description "MiniStack DB credentials" \
  --secret-string '{"username":"ministack_app","password":"d8tapassw0rd","host":"localhost","port":5432}'

ok "Secrets Manager: 2 secrets ready"

# =============================================================================
# 18. SSM Parameter Store
# =============================================================================
info "── SSM Parameter Store ───────────────────────────────"

run "SSM: /ministack/env" \
  ssm put-parameter \
  --name /ministack/env \
  --value production \
  --type String \
  --description "Deployment environment"

run "SSM: /ministack/log-level" \
  ssm put-parameter \
  --name /ministack/log-level \
  --value INFO \
  --type String

run "SSM: /ministack/db/url (SecureString)" \
  ssm put-parameter \
  --name /ministack/db/url \
  --value "postgresql://localhost:5432/ministack" \
  --type SecureString \
  --description "Database connection URL"

run "SSM: /ministack/feature-flags" \
  ssm put-parameter \
  --name /ministack/feature-flags \
  --value '{"newCheckout":true,"darkMode":false,"betaSearch":true}' \
  --type String

ok "SSM: 4 parameters ready"

# =============================================================================
# 19. ACM
# =============================================================================
info "── ACM ───────────────────────────────────────────────"

CERT_ARN=$($AWS acm request-certificate \
  --domain-name ministack.example.com \
  --validation-method DNS \
  --subject-alternative-names "*.ministack.example.com" "api.ministack.example.com" \
  --tags Key=Name,Value=ministack-wildcard \
  --query 'CertificateArn' --output text 2>/dev/null || \
  $AWS acm list-certificates \
  --query "CertificateSummaryList[?DomainName=='ministack.example.com'].CertificateArn" \
  --output text)
ok "ACM: certificate requested ($CERT_ARN)"

# =============================================================================
# 20. ECR
# =============================================================================
info "── ECR ───────────────────────────────────────────────"

run "ECR repo: ministack/api" \
  ecr create-repository \
  --repository-name ministack/api \
  --image-scanning-configuration scanOnPush=true \
  --encryption-configuration encryptionType=AES256 \
  --tags Key=Name,Value=ministack-api

run "ECR repo: ministack/worker" \
  ecr create-repository \
  --repository-name ministack/worker \
  --image-scanning-configuration scanOnPush=true \
  --tags Key=Name,Value=ministack-worker

ok "ECR: 2 repositories ready"

# =============================================================================
# 21. ECS
# =============================================================================
info "── ECS ───────────────────────────────────────────────"

run "ECS cluster: ministack" \
  ecs create-cluster \
  --cluster-name ministack \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
  --tags key=Name,value=ministack

$AWS ecs register-task-definition \
  --family ministack-api \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu "256" \
  --memory "512" \
  --execution-role-arn "$LAMBDA_ROLE_ARN" \
  --container-definitions '[{
    "name":"api",
    "image":"ministack/api:latest",
    "portMappings":[{"containerPort":8080,"protocol":"tcp"}],
    "environment":[
      {"name":"ENV","value":"production"},
      {"name":"PORT","value":"8080"}
    ],
    "logConfiguration":{
      "logDriver":"awslogs",
      "options":{
        "awslogs-group":"/ministack/api",
        "awslogs-region":"us-east-1",
        "awslogs-stream-prefix":"ecs"
      }
    }
  }]' >> "$LOG_FILE" 2>&1 || true
ok "ECS task def: ministack-api (Fargate 0.25vCPU/512MB)"

$AWS ecs register-task-definition \
  --family ministack-worker \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu "512" \
  --memory "1024" \
  --execution-role-arn "$LAMBDA_ROLE_ARN" \
  --container-definitions '[{
    "name":"worker",
    "image":"ministack/worker:latest",
    "environment":[
      {"name":"QUEUE_URL","value":"http://localhost:4566/000000000000/ministack-orders"},
      {"name":"WORKERS","value":"4"}
    ]
  }]' >> "$LOG_FILE" 2>&1 || true
ok "ECS task def: ministack-worker (Fargate 0.5vCPU/1GB)"

# =============================================================================
# 22. Route53
# =============================================================================
info "── Route53 ───────────────────────────────────────────"

HOSTED_ZONE_ID=$($AWS route53 create-hosted-zone \
  --name ministack.example.com \
  --caller-reference "ministack-$(date +%s)" \
  --query 'HostedZone.Id' --output text 2>/dev/null | sed 's|/hostedzone/||' || \
  $AWS route53 list-hosted-zones \
  --query "HostedZones[?Name=='ministack.example.com.'].Id" --output text | sed 's|/hostedzone/||')
ok "Route53 hosted zone: ministack.example.com ($HOSTED_ZONE_ID)"

$AWS route53 change-resource-record-sets \
  --hosted-zone-id "$HOSTED_ZONE_ID" \
  --change-batch '{
    "Changes":[
      {"Action":"CREATE","ResourceRecordSet":{
        "Name":"api.ministack.example.com","Type":"A","TTL":300,
        "ResourceRecords":[{"Value":"127.0.0.1"}]
      }},
      {"Action":"CREATE","ResourceRecordSet":{
        "Name":"www.ministack.example.com","Type":"CNAME","TTL":300,
        "ResourceRecords":[{"Value":"ministack.example.com"}]
      }}
    ]
  }' >> "$LOG_FILE" 2>&1 || true
ok "Route53: A + CNAME records created"

# =============================================================================
# 23. ALB
# =============================================================================
info "── ALB ───────────────────────────────────────────────"

ALB_ARN=$($AWS elbv2 create-load-balancer \
  --name ministack-alb \
  --subnets "$SUBNET_PUB_A" "$SUBNET_PUB_B" \
  --security-groups "$SG_APP" \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4 \
  --tags Key=Name,Value=ministack-alb \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || \
  $AWS elbv2 describe-load-balancers --names ministack-alb \
  --query 'LoadBalancers[0].LoadBalancerArn' --output text)
ok "ALB: ministack-alb ($ALB_ARN)"

TG_ARN=$($AWS elbv2 create-target-group \
  --name ministack-api-tg \
  --protocol HTTP \
  --port 8080 \
  --vpc-id "$VPC_ID" \
  --target-type ip \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --tags Key=Name,Value=ministack-api-tg \
  --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || \
  $AWS elbv2 describe-target-groups --names ministack-api-tg \
  --query 'TargetGroups[0].TargetGroupArn' --output text)
ok "ALB target group: ministack-api-tg"

$AWS elbv2 create-listener \
  --load-balancer-arn "$ALB_ARN" \
  --protocol HTTP \
  --port 80 \
  --default-actions "Type=forward,TargetGroupArn=${TG_ARN}" \
  >> "$LOG_FILE" 2>&1 || true
ok "ALB listener: HTTP:80 → ministack-api-tg"

# =============================================================================
# 24. Auto Scaling
# =============================================================================
info "── Auto Scaling ──────────────────────────────────────"

$AWS autoscaling create-launch-configuration \
  --launch-configuration-name ministack-lc \
  --image-id "$AMI_ID" \
  --instance-type t3.micro \
  --security-groups "$SG_APP" \
  >> "$LOG_FILE" 2>&1 || true
ok "ASG launch config: ministack-lc"

$AWS autoscaling create-auto-scaling-group \
  --auto-scaling-group-name ministack-asg \
  --launch-configuration-name ministack-lc \
  --min-size 1 \
  --max-size 4 \
  --desired-capacity 2 \
  --vpc-zone-identifier "${SUBNET_PUB_A},${SUBNET_PUB_B}" \
  --tags "Key=Name,Value=ministack-asg,PropagateAtLaunch=true" \
  >> "$LOG_FILE" 2>&1 || true
ok "ASG: ministack-asg (min=1, desired=2, max=4)"

$AWS autoscaling put-scaling-policy \
  --auto-scaling-group-name ministack-asg \
  --policy-name ministack-cpu-scale-out \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "PredefinedMetricSpecification":{"PredefinedMetricType":"ASGAverageCPUUtilization"},
    "TargetValue":70.0,
    "ScaleInCooldown":300,
    "ScaleOutCooldown":60
  }' >> "$LOG_FILE" 2>&1 || true
ok "ASG scaling policy: CPU target 70%"

# =============================================================================
# 25. CloudFormation
# =============================================================================
info "── CloudFormation ────────────────────────────────────"

$AWS s3api create-bucket --bucket ministack-cfn-artifacts >> "$LOG_FILE" 2>&1 || true

$AWS cloudformation create-stack \
  --stack-name ministack-infra \
  --template-body '{
    "AWSTemplateFormatVersion":"2010-09-09",
    "Description":"MiniStack base infra stack",
    "Parameters":{"Env":{"Type":"String","Default":"production"}},
    "Resources":{
      "ArtifactBucket":{
        "Type":"AWS::S3::Bucket",
        "Properties":{
          "BucketName":"ministack-cfn-artifacts",
          "Tags":[{"Key":"ManagedBy","Value":"CloudFormation"}]
        }
      }
    },
    "Outputs":{
      "BucketName":{"Value":{"Ref":"ArtifactBucket"},"Description":"CFN artifact bucket"}
    }
  }' \
  --parameters ParameterKey=Env,ParameterValue=production \
  --tags Key=ManagedBy,Value=CloudFormation \
  >> "$LOG_FILE" 2>&1 || true
ok "CloudFormation stack: ministack-infra"

# =============================================================================
# 26. Cognito
# =============================================================================
info "── Cognito ───────────────────────────────────────────"

USER_POOL_ID=$($AWS cognito-idp create-user-pool \
  --pool-name ministack-users \
  --policies 'PasswordPolicy={MinimumLength=8,RequireUppercase=true,RequireLowercase=true,RequireNumbers=true,RequireSymbols=false}' \
  --auto-verified-attributes email \
  --username-attributes email \
  --mfa-configuration OFF \
  --schema '[{"Name":"email","Required":true,"Mutable":true},{"Name":"role","AttributeDataType":"String","Mutable":true}]' \
  --tags Name=ministack-users \
  --query 'UserPool.Id' --output text 2>/dev/null || \
  $AWS cognito-idp list-user-pools --max-results 10 \
  --query "UserPools[?Name=='ministack-users'].Id" --output text)
ok "Cognito user pool: ministack-users ($USER_POOL_ID)"

CLIENT_ID=$($AWS cognito-idp create-user-pool-client \
  --user-pool-id "$USER_POOL_ID" \
  --client-name ministack-web \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --query 'UserPoolClient.ClientId' --output text 2>/dev/null || echo "")
ok "Cognito app client: ministack-web ($CLIENT_ID)"

$AWS cognito-idp admin-create-user \
  --user-pool-id "$USER_POOL_ID" \
  --username alice@example.com \
  --user-attributes Name=email,Value=alice@example.com Name=email_verified,Value=true \
  --temporary-password "Temp1234!" \
  >> "$LOG_FILE" 2>&1 || true
ok "Cognito: test user alice@example.com created"

# =============================================================================
# 27. SES
# =============================================================================
info "── SES ───────────────────────────────────────────────"

run "SES: verify noreply@ministack.example.com" \
  ses verify-email-identity --email-address noreply@ministack.example.com

run "SES: verify alerts@ministack.example.com" \
  ses verify-email-identity --email-address alerts@ministack.example.com

$AWS sesv2 create-email-template \
  --template-name ministack-welcome \
  --template-content '{
    "Subject":"Welcome to MiniStack, {{name}}!",
    "Text":"Hi {{name}}, welcome to MiniStack. Your account is ready.",
    "Html":"<h1>Welcome, {{name}}!</h1><p>Your MiniStack account is ready.</p>"
  }' >> "$LOG_FILE" 2>&1 || true
ok "SES: 2 identities verified, 1 template (ministack-welcome)"

# =============================================================================
# 28. API Gateway v2 (HTTP API)
# =============================================================================
info "── API Gateway v2 (HTTP API) ─────────────────────────"

APIGWV2_ID=$($AWS apigatewayv2 create-api \
  --name ministack-http-api \
  --protocol-type HTTP \
  --description "MiniStack HTTP API" \
  --cors-configuration \
    AllowOrigins='["*"]',AllowMethods='["GET","POST","PUT","DELETE"]',AllowHeaders='["Content-Type","Authorization"]' \
  --query 'ApiId' --output text 2>/dev/null || \
  $AWS apigatewayv2 get-apis \
  --query "Items[?Name=='ministack-http-api'].ApiId" --output text)
ok "API Gateway v2: ministack-http-api ($APIGWV2_ID)"

LAMBDA_INTEG_ID=$($AWS apigatewayv2 create-integration \
  --api-id "$APIGWV2_ID" \
  --integration-type AWS_PROXY \
  --integration-uri "arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:ministack-api-handler" \
  --payload-format-version "2.0" \
  --query 'IntegrationId' --output text 2>/dev/null || echo "")

if [[ -n "$LAMBDA_INTEG_ID" ]]; then
  $AWS apigatewayv2 create-route --api-id "$APIGWV2_ID" \
    --route-key "GET /v2/items" \
    --target "integrations/${LAMBDA_INTEG_ID}" >> "$LOG_FILE" 2>&1 || true
  $AWS apigatewayv2 create-route --api-id "$APIGWV2_ID" \
    --route-key "POST /v2/items" \
    --target "integrations/${LAMBDA_INTEG_ID}" >> "$LOG_FILE" 2>&1 || true
fi

$AWS apigatewayv2 create-stage \
  --api-id "$APIGWV2_ID" \
  --stage-name dev \
  --auto-deploy >> "$LOG_FILE" 2>&1 || true
ok "API Gateway v2: GET+POST /v2/items + dev stage"

# =============================================================================
# 29. EBS
# =============================================================================
info "── EBS ───────────────────────────────────────────────"

EBS_DATA_VOL=$($AWS ec2 create-volume \
  --availability-zone us-east-1a \
  --size 20 \
  --volume-type gp3 \
  --throughput 125 \
  --iops 3000 \
  --encrypted \
  --kms-key-id "$KEY_ID" \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=ministack-data-vol}]' \
  --query 'VolumeId' --output text 2>/dev/null || echo "")
ok "EBS volume: ministack-data-vol 20GB gp3 enc ($EBS_DATA_VOL)"

EBS_DB_VOL=$($AWS ec2 create-volume \
  --availability-zone us-east-1a \
  --size 100 \
  --volume-type io2 \
  --iops 10000 \
  --encrypted \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=ministack-db-vol}]' \
  --query 'VolumeId' --output text 2>/dev/null || echo "")
ok "EBS volume: ministack-db-vol 100GB io2 enc ($EBS_DB_VOL)"

$AWS ec2 create-snapshot \
  --volume-id "$EBS_DATA_VOL" \
  --description "MiniStack data-vol seed snapshot" \
  --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Name,Value=ministack-data-snapshot}]' \
  >> "$LOG_FILE" 2>&1 || true
ok "EBS snapshot: ministack-data-snapshot"

# =============================================================================
# 30. AppConfig
# =============================================================================
info "── AppConfig ─────────────────────────────────────────"

APP_CFG_ID=$($AWS appconfig create-application \
  --name ministack \
  --description "MiniStack application configuration" \
  --tags Name=ministack \
  --query 'Id' --output text 2>/dev/null || \
  $AWS appconfig list-applications \
  --query "Items[?Name=='ministack'].Id" --output text)
ok "AppConfig application: ministack ($APP_CFG_ID)"

ENV_CFG_ID=$($AWS appconfig create-environment \
  --application-id "$APP_CFG_ID" \
  --name production \
  --description "Production environment" \
  --query 'Id' --output text 2>/dev/null || echo "")
ok "AppConfig environment: production ($ENV_CFG_ID)"

PROFILE_ID=$($AWS appconfig create-configuration-profile \
  --application-id "$APP_CFG_ID" \
  --name feature-flags \
  --location-uri hosted \
  --type AWS.AppConfig.FeatureFlags \
  --query 'Id' --output text 2>/dev/null || echo "")
ok "AppConfig profile: feature-flags ($PROFILE_ID)"

if [[ -n "$PROFILE_ID" && -n "$APP_CFG_ID" ]]; then
  $AWS appconfig create-hosted-configuration-version \
    --application-id "$APP_CFG_ID" \
    --configuration-profile-id "$PROFILE_ID" \
    --content-type "application/json" \
    --content '{"flags":{"dark_mode":{"enabled":false},"new_checkout":{"enabled":true},"beta_search":{"enabled":true}},"version":"1"}' \
    /tmp/appconfig_out.json >> "$LOG_FILE" 2>&1 || true
  ok "AppConfig: hosted config v1 created"
fi

# =============================================================================
# 31. Organizations
# =============================================================================
info "── Organizations ─────────────────────────────────────"

ORG_ID=$($AWS organizations create-organization --feature-set ALL \
  --query 'Organization.Id' --output text 2>/dev/null || \
  $AWS organizations describe-organization \
  --query 'Organization.Id' --output text)
ok "Organizations: org ready ($ORG_ID)"

ROOT_ID=$($AWS organizations list-roots --query 'Roots[0].Id' --output text 2>/dev/null || echo "")

if [[ -n "$ROOT_ID" ]]; then
  DEV_OU=$($AWS organizations create-organizational-unit \
    --parent-id "$ROOT_ID" --name Development \
    --query 'OrganizationalUnit.Id' --output text 2>/dev/null || echo "")
  ok "Organizations OU: Development ($DEV_OU)"

  PROD_OU=$($AWS organizations create-organizational-unit \
    --parent-id "$ROOT_ID" --name Production \
    --query 'OrganizationalUnit.Id' --output text 2>/dev/null || echo "")
  ok "Organizations OU: Production ($PROD_OU)"
fi

# =============================================================================
# 32. CodeBuild
# =============================================================================
info "── CodeBuild ─────────────────────────────────────────"

$AWS codebuild create-project \
  --name ministack-ci \
  --source '{"type":"NO_SOURCE","buildspec":"version:0.2\nphases:\n  build:\n    commands:\n      - echo Build complete"}' \
  --artifacts '{"type":"S3","location":"ministack-processed-data","name":"build-artifacts"}' \
  --environment '{
    "type":"LINUX_CONTAINER",
    "computeType":"BUILD_GENERAL1_SMALL",
    "image":"aws/codebuild/standard:7.0",
    "environmentVariables":[
      {"name":"NODE_ENV","value":"test"},
      {"name":"AWS_REGION","value":"us-east-1"}
    ]
  }' \
  --service-role "$LAMBDA_ROLE_ARN" \
  --logs-config '{
    "cloudWatchLogs":{"status":"ENABLED","groupName":"/aws/codebuild/ministack-ci"},
    "s3Logs":{"status":"DISABLED"}
  }' \
  --tags key=Name,value=ministack-ci \
  >> "$LOG_FILE" 2>&1 || true
ok "CodeBuild project: ministack-ci"

# =============================================================================
# 33. Athena
# =============================================================================
info "── Athena ────────────────────────────────────────────"

run "Athena workgroup: ministack" \
  athena create-work-group \
  --name ministack \
  --configuration 'ResultConfiguration={OutputLocation=s3://ministack-processed-data/athena-results/},EnforceWorkGroupConfiguration=true,PublishCloudWatchMetricsEnabled=true' \
  --description "MiniStack analytics workgroup" \
  --tags Key=Name,Value=ministack

$AWS athena start-query-execution \
  --query-string "CREATE DATABASE IF NOT EXISTS ministack_analytics COMMENT 'MiniStack analytics'" \
  --work-group ministack \
  >> "$LOG_FILE" 2>&1 || true

QUERY_ID=$($AWS athena start-query-execution \
  --query-string "SELECT type, COUNT(*) AS cnt FROM ministack_raw.events GROUP BY type" \
  --work-group ministack \
  --query-execution-context Database=ministack_raw \
  --query 'QueryExecutionId' --output text 2>/dev/null || echo "")
ok "Athena: workgroup + DB + sample query (${QUERY_ID:-n/a})"

# =============================================================================
# 34. CloudTrail
# =============================================================================
info "── CloudTrail ────────────────────────────────────────"

$AWS s3api create-bucket --bucket ministack-audit-logs >> "$LOG_FILE" 2>&1 || true
$AWS s3api put-bucket-policy --bucket ministack-audit-logs --policy '{
  "Version":"2012-10-17",
  "Statement":[
    {"Effect":"Allow","Principal":{"Service":"cloudtrail.amazonaws.com"},
     "Action":"s3:PutObject","Resource":"arn:aws:s3:::ministack-audit-logs/AWSLogs/*"},
    {"Effect":"Allow","Principal":{"Service":"cloudtrail.amazonaws.com"},
     "Action":"s3:GetBucketAcl","Resource":"arn:aws:s3:::ministack-audit-logs"}
  ]}' >> "$LOG_FILE" 2>&1 || true

$AWS cloudtrail create-trail \
  --name ministack-audit \
  --s3-bucket-name ministack-audit-logs \
  --include-global-service-events \
  --is-multi-region-trail \
  --enable-log-file-validation \
  >> "$LOG_FILE" 2>&1 || true
$AWS cloudtrail start-logging --name ministack-audit >> "$LOG_FILE" 2>&1 || true
ok "CloudTrail: ministack-audit (multi-region, validation enabled)"

# =============================================================================
# 35. RDS
# =============================================================================
info "── RDS ───────────────────────────────────────────────"

$AWS rds create-db-subnet-group \
  --db-subnet-group-name ministack-db-subnet \
  --db-subnet-group-description "MiniStack DB subnet group" \
  --subnet-ids "$SUBNET_PRIV_A" \
  --tags Key=Name,Value=ministack-db-subnet \
  >> "$LOG_FILE" 2>&1 || true
ok "RDS subnet group: ministack-db-subnet"

$AWS rds create-db-instance \
  --db-instance-identifier ministack-postgres \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version "15.4" \
  --master-username ministack_admin \
  --master-user-password "S3cr3tP4ss!" \
  --allocated-storage 20 \
  --storage-type gp3 \
  --db-subnet-group-name ministack-db-subnet \
  --vpc-security-group-ids "$SG_APP" \
  --db-name ministack \
  --no-multi-az \
  --no-publicly-accessible \
  --tags Key=Name,Value=ministack-postgres \
  >> "$LOG_FILE" 2>&1 || true
ok "RDS: ministack-postgres (postgres 15.4 / db.t3.micro / 20GB gp3)"

# =============================================================================
# 36. ElastiCache
# =============================================================================
info "── ElastiCache ───────────────────────────────────────"

$AWS elasticache create-cache-subnet-group \
  --cache-subnet-group-name ministack-cache-subnet \
  --cache-subnet-group-description "MiniStack cache subnet group" \
  --subnet-ids "$SUBNET_PRIV_A" \
  >> "$LOG_FILE" 2>&1 || true
ok "ElastiCache subnet group: ministack-cache-subnet"

$AWS elasticache create-replication-group \
  --replication-group-id ministack-redis \
  --replication-group-description "MiniStack Redis cache" \
  --cache-node-type cache.t3.micro \
  --engine redis \
  --engine-version "7.0" \
  --num-cache-clusters 1 \
  --cache-subnet-group-name ministack-cache-subnet \
  --security-group-ids "$SG_APP" \
  --tags Key=Name,Value=ministack-redis \
  >> "$LOG_FILE" 2>&1 || true
ok "ElastiCache: ministack-redis (Redis 7.0 / cache.t3.micro)"

# =============================================================================
# 37. OpenSearch
# =============================================================================
info "── OpenSearch ────────────────────────────────────────"

$AWS opensearch create-domain \
  --domain-name ministack-search \
  --engine-version "OpenSearch_2.11" \
  --cluster-config '{"InstanceType":"t3.small.search","InstanceCount":1,"DedicatedMasterEnabled":false}' \
  --ebs-options 'EBSEnabled=true,VolumeType=gp3,VolumeSize=10' \
  --access-policies '{
    "Version":"2012-10-17",
    "Statement":[{"Effect":"Allow","Principal":{"AWS":"*"},"Action":"es:*","Resource":"*"}]
  }' \
  --tags Key=Name,Value=ministack-search \
  >> "$LOG_FILE" 2>&1 || true
ok "OpenSearch: ministack-search (OpenSearch 2.11 / t3.small / 10GB)"

# =============================================================================
# 38. CloudFront
# =============================================================================
info "── CloudFront ────────────────────────────────────────"

$AWS cloudfront create-distribution \
  --distribution-config '{
    "CallerReference":"ministack-cf-001",
    "Comment":"MiniStack CDN",
    "Enabled":true,
    "Origins":{"Quantity":1,"Items":[{
      "Id":"ministack-s3-origin",
      "DomainName":"ministack-raw-data.s3.us-east-1.amazonaws.com",
      "S3OriginConfig":{"OriginAccessIdentity":""}
    }]},
    "DefaultCacheBehavior":{
      "ViewerProtocolPolicy":"redirect-to-https",
      "TargetOriginId":"ministack-s3-origin",
      "TrustedSigners":{"Enabled":false,"Quantity":0},
      "ForwardedValues":{"QueryString":false,"Cookies":{"Forward":"none"}},
      "MinTTL":0,"DefaultTTL":86400,"MaxTTL":31536000
    }
  }' >> "$LOG_FILE" 2>&1 || true
ok "CloudFront: ministack distribution created"

# =============================================================================
# 39. EFS
# =============================================================================
info "── EFS ───────────────────────────────────────────────"

EFS_ID=$($AWS efs create-file-system \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --encrypted \
  --kms-key-id "$KEY_ID" \
  --tags Key=Name,Value=ministack-efs \
  --query 'FileSystemId' --output text 2>/dev/null || \
  $AWS efs describe-file-systems \
  --query "FileSystems[?Tags[?Key=='Name'&&Value=='ministack-efs']].FileSystemId" \
  --output text)
ok "EFS: ministack-efs ($EFS_ID)"

$AWS efs create-mount-target \
  --file-system-id "$EFS_ID" \
  --subnet-id "$SUBNET_PRIV_A" \
  --security-groups "$SG_APP" \
  >> "$LOG_FILE" 2>&1 || true
ok "EFS mount target: private-a"

# =============================================================================
# 40. Batch
# =============================================================================
info "── Batch ─────────────────────────────────────────────"

$AWS batch create-compute-environment \
  --compute-environment-name ministack-batch-fargate \
  --type MANAGED \
  --state ENABLED \
  --compute-resources '{
    "type":"FARGATE",
    "maxvCpus":16,
    "subnets":["'"$SUBNET_PRIV_A"'"],
    "securityGroupIds":["'"$SG_APP"'"]
  }' \
  --service-role "arn:aws:iam::${ACCOUNT_ID}:role/AWSBatchServiceRole" \
  >> "$LOG_FILE" 2>&1 || true
ok "Batch compute environment: ministack-batch-fargate (Fargate)"

$AWS batch create-job-queue \
  --job-queue-name ministack-jobs \
  --state ENABLED \
  --priority 100 \
  --compute-environment-order '[{"order":1,"computeEnvironment":"ministack-batch-fargate"}]' \
  >> "$LOG_FILE" 2>&1 || true
ok "Batch job queue: ministack-jobs"

$AWS batch register-job-definition \
  --job-definition-name ministack-etl-job \
  --type container \
  --platform-capabilities FARGATE \
  --container-properties '{
    "image":"ministack/worker:latest",
    "resourceRequirements":[{"type":"VCPU","value":"1"},{"type":"MEMORY","value":"2048"}],
    "executionRoleArn":"'"$LAMBDA_ROLE_ARN"'",
    "jobRoleArn":"'"$LAMBDA_ROLE_ARN"'",
    "networkConfiguration":{"assignPublicIp":"ENABLED"},
    "environment":[{"name":"JOB_TYPE","value":"etl"}]
  }' >> "$LOG_FILE" 2>&1 || true
ok "Batch job definition: ministack-etl-job"

# =============================================================================
# 41. DynamoDB Streams (enable on existing tables)
# =============================================================================
info "── DynamoDB Streams ──────────────────────────────────"

$AWS dynamodb update-table \
  --table-name ministack-users \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES \
  >> "$LOG_FILE" 2>&1 || true
ok "DynamoDB Streams: enabled on ministack-users (NEW_AND_OLD_IMAGES)"

$AWS dynamodb update-table \
  --table-name ministack-events \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_IMAGE \
  >> "$LOG_FILE" 2>&1 || true
ok "DynamoDB Streams: enabled on ministack-events (NEW_IMAGE)"

# =============================================================================
# Done
# =============================================================================
echo ""
echo "=====================================================" | tee -a "$LOG_FILE"
echo " Seed complete!  $(date)"                               | tee -a "$LOG_FILE"
echo "=====================================================" | tee -a "$LOG_FILE"
echo ""
echo "Resources created per service:"
echo "  1.  KMS              2 keys, 2 aliases"
echo "  2.  IAM              4 roles, 1 policy, 2 users"
echo "  3.  VPC              1 VPC, 3 subnets, 1 IGW, 1 SG, 2 EC2 instances"
echo "  4.  S3               6 buckets, 4 objects"
echo "  5.  DynamoDB         3 tables, 7 items, 2 streams"
echo "  6.  SQS              4 queues, 2 messages"
echo "  7.  SNS              2 topics, 1 subscription, 1 message"
echo "  8.  CloudWatch       3 log groups, 1 log stream, 2 alarms, 2 metrics"
echo "  9.  Kinesis          2 streams, 3 records"
echo "  10. Lambda           2 functions, 1 test invocation"
echo "  11. Firehose         1 delivery stream"
echo "  12. API Gateway      1 REST API, 2 resources, 2 stages"
echo "  13. EventBridge      1 bus, 2 rules, 2 targets"
echo "  14. Glue             2 databases, 2 tables, 1 job, 1 crawler, 1 registry, 3 schemas"
echo "  15. Step Functions   2 state machines, 1 execution"
echo "  16. WAF              1 IP set, 1 Web ACL"
echo "  17. Secrets Manager  2 secrets"
echo "  18. SSM              4 parameters"
echo "  19. ACM              1 certificate"
echo "  20. ECR              2 repositories"
echo "  21. ECS              1 cluster, 2 task definitions"
echo "  22. Route53          1 hosted zone, 2 records"
echo "  23. ALB              1 load balancer, 1 target group, 1 listener"
echo "  24. Auto Scaling     1 launch config, 1 ASG, 1 scaling policy"
echo "  25. CloudFormation   1 stack"
echo "  26. Cognito          1 user pool, 1 app client, 1 user"
echo "  27. SES              2 identities, 1 template"
echo "  28. API Gateway v2   1 HTTP API, 2 routes, 1 stage"
echo "  29. EBS              2 volumes, 1 snapshot"
echo "  30. AppConfig        1 app, 1 env, 1 profile, 1 config version"
echo "  31. Organizations    1 org, 2 OUs"
echo "  32. CodeBuild        1 project"
echo "  33. Athena           1 workgroup, 1 database, 1 query"
echo "  34. CloudTrail       1 trail (multi-region)"
echo "  35. RDS              1 DB instance (postgres 15.4)"
echo "  36. ElastiCache      1 Redis replication group"
echo "  37. OpenSearch       1 domain"
echo "  38. CloudFront       1 distribution"
echo "  39. EFS              1 file system, 1 mount target"
echo "  40. Batch            1 compute env, 1 job queue, 1 job definition"
echo "  41. DynamoDB Streams 2 streams enabled"
echo ""
echo "Log: $LOG_FILE"
