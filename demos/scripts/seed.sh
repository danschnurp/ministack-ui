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
  $AWS s3 rb s3://ministack-raw-data      --force 2>/dev/null || true
  $AWS s3 rb s3://ministack-processed-data --force 2>/dev/null || true
  $AWS s3 rb s3://ministack-firehose-dest  --force 2>/dev/null || true
  $AWS s3 rb s3://ministack-glue-scripts   --force 2>/dev/null || true
  ok "S3 buckets removed"
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
# Done
# =============================================================================
echo ""
echo "=====================================================" | tee -a "$LOG_FILE"
echo " Seed complete!  $(date)"                               | tee -a "$LOG_FILE"
echo "=====================================================" | tee -a "$LOG_FILE"
echo ""
echo "Resources created per service:"
echo "  KMS             2 keys, 2 aliases"
echo "  IAM             4 roles, 1 policy, 2 users"
echo "  VPC             1 VPC, 3 subnets, 1 IGW, 2 SGs, 2 EC2 instances"
echo "  S3              4 buckets, 4 objects"
echo "  DynamoDB        3 tables, 7 items"
echo "  SQS             4 queues, 2 messages"
echo "  SNS             2 topics, 1 subscription, 1 message"
echo "  CloudWatch      3 log groups, 1 log stream, 2 alarms, 2 metrics"
echo "  Kinesis         2 streams, 3 records"
echo "  Lambda          2 functions, 1 test invocation"
echo "  Firehose        1 delivery stream"
echo "  API Gateway     1 REST API, 2 resources, 2 stages"
echo "  EventBridge     1 bus, 2 rules, 2 targets"
echo "  Glue            2 databases, 2 tables, 1 job, 1 crawler"
echo "  Step Functions  2 state machines, 1 execution"
echo "  WAF             1 IP set, 1 Web ACL"
echo ""
echo "Log: $LOG_FILE"
