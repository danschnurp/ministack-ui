###############################################################################
# MiniStack – LocalStack / OpenTofu seed
###############################################################################

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.0"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    apigateway     = "http://localhost:4566"
    cloudwatch     = "http://localhost:4566"
    dynamodb       = "http://localhost:4566"
    ec2            = "http://localhost:4566"
    eventbridge    = "http://localhost:4566"
    firehose       = "http://localhost:4566"
    glue           = "http://localhost:4566"
    iam            = "http://localhost:4566"
    kinesis        = "http://localhost:4566"
    kms            = "http://localhost:4566"
    lambda         = "http://localhost:4566"
    s3             = "http://localhost:4566"
    sns            = "http://localhost:4566"
    sqs            = "http://localhost:4566"
    sfn            = "http://localhost:4566"
    wafv2          = "http://localhost:4566"
    logs           = "http://localhost:4566"
  }
}

###############################################################################
# KMS
###############################################################################

resource "aws_kms_key" "main" {
  description             = "MiniStack main encryption key"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  tags                    = { Name = "ministack-main" }
}

resource "aws_kms_alias" "main" {
  name          = "alias/ministack-main"
  target_key_id = aws_kms_key.main.key_id
}

resource "aws_kms_key" "s3" {
  description             = "MiniStack S3 encryption key"
  deletion_window_in_days = 7
  tags                    = { Name = "ministack-s3" }
}

resource "aws_kms_alias" "s3" {
  name          = "alias/ministack-s3"
  target_key_id = aws_kms_key.s3.key_id
}

###############################################################################
# IAM
###############################################################################

locals {
  trust_lambda = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  trust_glue = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  trust_sfn = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "states.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  trust_firehose = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "firehose.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  ami_id = "ami-0c55b159cbfafe1d0"
}

resource "aws_iam_role" "lambda_exec" {
  name               = "ministack-lambda-exec"
  assume_role_policy = local.trust_lambda
  tags               = { Name = "ministack-lambda-exec" }
}

resource "aws_iam_role" "glue_service" {
  name               = "ministack-glue-service"
  assume_role_policy = local.trust_glue
  tags               = { Name = "ministack-glue-service" }
}

resource "aws_iam_role" "sfn_exec" {
  name               = "ministack-sfn-exec"
  assume_role_policy = local.trust_sfn
  tags               = { Name = "ministack-sfn-exec" }
}

resource "aws_iam_role" "firehose_delivery" {
  name               = "ministack-firehose-delivery"
  assume_role_policy = local.trust_firehose
  tags               = { Name = "ministack-firehose-delivery" }
}

resource "aws_iam_policy" "lambda_basic" {
  name = "ministack-lambda-basic"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["kinesis:*", "dynamodb:*", "sqs:*", "sns:*"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy" "glue_basic" {
  name = "ministack-glue-basic"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:*", "logs:*", "glue:*"]
      Resource = "*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_basic.arn
}

resource "aws_iam_role_policy_attachment" "glue_basic" {
  role       = aws_iam_role.glue_service.name
  policy_arn = aws_iam_policy.glue_basic.arn
}

resource "aws_iam_user" "app_user" {
  name = "ministack-app"
  tags = { Name = "ministack-app" }
}

resource "aws_iam_user" "readonly_user" {
  name = "ministack-readonly"
  tags = { Name = "ministack-readonly" }
}

###############################################################################
# VPC
###############################################################################

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "ministack-vpc" }
}

resource "aws_subnet" "public_a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
  tags                    = { Name = "ministack-public-a" }
}

resource "aws_subnet" "public_b" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true
  tags                    = { Name = "ministack-public-b" }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "us-east-1a"
  tags              = { Name = "ministack-private-a" }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "ministack-igw" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = { Name = "ministack-public-rt" }
}

resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "app" {
  name        = "ministack-app-sg"
  description = "MiniStack application security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "ministack-app-sg" }
}

resource "aws_security_group" "db" {
  name        = "ministack-db-sg"
  description = "MiniStack database security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }

  tags = { Name = "ministack-db-sg" }
}

###############################################################################
# EC2
###############################################################################

resource "aws_instance" "web" {
  ami                    = local.ami_id
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.public_a.id
  vpc_security_group_ids = [aws_security_group.app.id]
  tags                   = { Name = "ministack-web", Role = "web" }
}

resource "aws_instance" "worker" {
  ami                    = local.ami_id
  instance_type          = "t3.small"
  subnet_id              = aws_subnet.private_a.id
  vpc_security_group_ids = [aws_security_group.app.id]
  tags                   = { Name = "ministack-worker", Role = "worker" }
}

###############################################################################
# S3
###############################################################################

resource "aws_s3_bucket" "raw" {
  bucket        = "ministack-raw-data"
  force_destroy = true
  tags          = { Name = "ministack-raw-data", Tier = "raw" }
}

resource "aws_s3_bucket" "processed" {
  bucket        = "ministack-processed-data"
  force_destroy = true
  tags          = { Name = "ministack-processed-data", Tier = "processed" }
}

resource "aws_s3_bucket" "firehose_dest" {
  bucket        = "ministack-firehose-dest"
  force_destroy = true
  tags          = { Name = "ministack-firehose-dest", Tier = "firehose" }
}

resource "aws_s3_bucket" "glue_scripts" {
  bucket        = "ministack-glue-scripts"
  force_destroy = true
  tags          = { Name = "ministack-glue-scripts" }
}

resource "aws_s3_object" "sample_json" {
  bucket       = aws_s3_bucket.raw.id
  key          = "events/sample.json"
  content      = jsonencode({ id = "evt-001", type = "click", ts = "2024-01-15T10:00:00Z" })
  content_type = "application/json"
}

resource "aws_s3_object" "sample_csv" {
  bucket       = aws_s3_bucket.raw.id
  key          = "exports/users.csv"
  content      = "id,name,email\n1,Alice,alice@example.com\n2,Bob,bob@example.com\n3,Carol,carol@example.com"
  content_type = "text/csv"
}

resource "aws_s3_object" "glue_script" {
  bucket       = aws_s3_bucket.glue_scripts.id
  key          = "scripts/etl_job.py"
  content      = <<-PY
    import sys
    from awsglue.transforms import *
    from awsglue.utils import getResolvedOptions
    from pyspark.context import SparkContext
    from awsglue.context import GlueContext

    args = getResolvedOptions(sys.argv, ['JOB_NAME'])
    sc = SparkContext()
    glueContext = GlueContext(sc)
    print("MiniStack ETL job started:", args['JOB_NAME'])
  PY
  content_type = "text/x-python"
}

###############################################################################
# DynamoDB
###############################################################################

resource "aws_dynamodb_table" "users" {
  name         = "ministack-users"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"

  attribute {
    name = "userId"
    type = "S"
  }

  tags = { Name = "ministack-users" }
}

resource "aws_dynamodb_table" "events" {
  name         = "ministack-events"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "eventId"
  range_key    = "timestamp"

  attribute {
    name = "eventId"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  ttl {
    attribute_name = "expiresAt"
    enabled        = true
  }

  tags = { Name = "ministack-events" }
}

resource "aws_dynamodb_table" "orders" {
  name         = "ministack-orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "orderId"

  attribute {
    name = "orderId"
    type = "S"
  }

  tags = { Name = "ministack-orders" }
}

resource "aws_dynamodb_table_item" "user_alice" {
  table_name = aws_dynamodb_table.users.name
  hash_key   = aws_dynamodb_table.users.hash_key
  item = jsonencode({
    userId = { S = "user-001" }
    name   = { S = "Alice Smith" }
    email  = { S = "alice@example.com" }
    role   = { S = "admin" }
    active = { BOOL = true }
  })
}

resource "aws_dynamodb_table_item" "user_bob" {
  table_name = aws_dynamodb_table.users.name
  hash_key   = aws_dynamodb_table.users.hash_key
  item = jsonencode({
    userId = { S = "user-002" }
    name   = { S = "Bob Jones" }
    email  = { S = "bob@example.com" }
    role   = { S = "viewer" }
    active = { BOOL = true }
  })
}

###############################################################################
# SQS
###############################################################################

resource "aws_sqs_queue" "orders_dlq" {
  name                      = "ministack-orders-dlq"
  message_retention_seconds = 1209600
  tags                      = { Name = "ministack-orders-dlq" }
}

resource "aws_sqs_queue" "orders" {
  name                       = "ministack-orders"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 86400
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.orders_dlq.arn
    maxReceiveCount     = 3
  })
  tags = { Name = "ministack-orders" }
}

resource "aws_sqs_queue" "notifications" {
  name = "ministack-notifications"
  tags = { Name = "ministack-notifications" }
}

resource "aws_sqs_queue" "fifo_tasks" {
  name                        = "ministack-tasks.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  tags                        = { Name = "ministack-tasks" }
}

###############################################################################
# SNS
###############################################################################

resource "aws_sns_topic" "alerts" {
  name = "ministack-alerts"
  tags = { Name = "ministack-alerts" }
}

resource "aws_sns_topic" "events" {
  name = "ministack-events"
  tags = { Name = "ministack-events" }
}

resource "aws_sns_topic_subscription" "alerts_to_sqs" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.notifications.arn
}

###############################################################################
# CloudWatch
###############################################################################

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ministack/app"
  retention_in_days = 7
  tags              = { Name = "ministack-app-logs" }
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/ministack-processor"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ministack/api"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_stream" "app_main" {
  name           = "main"
  log_group_name = aws_cloudwatch_log_group.app.name
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "ministack-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda error rate too high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  tags                = { Name = "ministack-lambda-errors" }
}

resource "aws_cloudwatch_metric_alarm" "sqs_depth" {
  alarm_name          = "ministack-sqs-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = 100
  dimensions          = { QueueName = aws_sqs_queue.orders.name }
  tags                = { Name = "ministack-sqs-depth" }
}

###############################################################################
# Kinesis Data Stream
###############################################################################

resource "aws_kinesis_stream" "events" {
  name             = "ministack-events"
  shard_count      = 2
  retention_period = 24
  tags             = { Name = "ministack-events" }
}

resource "aws_kinesis_stream" "clickstream" {
  name             = "ministack-clickstream"
  shard_count      = 1
  retention_period = 48
  tags             = { Name = "ministack-clickstream" }
}

###############################################################################
# Kinesis Firehose
# FIX: buffering_hints is not a nested block in extended_s3_configuration —
#      use the top-level buffering_* arguments instead.
###############################################################################

resource "aws_kinesis_firehose_delivery_stream" "s3_delivery" {
  name        = "ministack-s3-delivery"
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn            = aws_iam_role.firehose_delivery.arn
    bucket_arn          = aws_s3_bucket.firehose_dest.arn
    prefix              = "events/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"
    compression_format  = "GZIP"
    buffering_size      = 5
    buffering_interval  = 60
  }

  tags = { Name = "ministack-s3-delivery" }
}

###############################################################################
# Lambda
# FIX: JS template literals use ${} which Terraform interprets as interpolation.
#      Replaced with string concatenation so no ${ } appears inside heredocs.
###############################################################################

data "archive_file" "processor_zip" {
  type        = "zip"
  output_path = "/tmp/ministack-processor.zip"
  source {
    content  = <<-JS
      exports.handler = async (event) => {
        console.log('MiniStack processor received:', JSON.stringify(event));
        const records = event.Records != null ? event.Records : [event];
        const processed = records.map(function(r) {
          return { id: r.messageId != null ? r.messageId : 'evt', processed: true, ts: Date.now() };
        });
        return { statusCode: 200, body: JSON.stringify({ processed: processed }) };
      };
    JS
    filename = "index.js"
  }
}

data "archive_file" "api_handler_zip" {
  type        = "zip"
  output_path = "/tmp/ministack-api-handler.zip"
  source {
    content  = <<-JS
      exports.handler = async (event) => {
        var path   = event.path   != null ? event.path   : '/';
        var method = event.httpMethod != null ? event.httpMethod : 'GET';
        console.log('MiniStack API: ' + method + ' ' + path);
        return {
          statusCode: 200,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ service: 'ministack-api', path: path, method: method, ts: new Date().toISOString() })
        };
      };
    JS
    filename = "index.js"
  }
}

resource "aws_lambda_function" "processor" {
  function_name    = "ministack-processor"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "index.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.processor_zip.output_path
  source_code_hash = data.archive_file.processor_zip.output_base64sha256
  timeout          = 30
  memory_size      = 256

  environment {
    variables = {
      ORDERS_TABLE  = aws_dynamodb_table.orders.name
      EVENTS_STREAM = aws_kinesis_stream.events.name
      ALERTS_TOPIC  = aws_sns_topic.alerts.arn
    }
  }

  tags = { Name = "ministack-processor" }
}

resource "aws_lambda_function" "api_handler" {
  function_name    = "ministack-api-handler"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "index.handler"
  runtime          = "nodejs20.x"
  filename         = data.archive_file.api_handler_zip.output_path
  source_code_hash = data.archive_file.api_handler_zip.output_base64sha256
  timeout          = 15
  memory_size      = 128
  tags             = { Name = "ministack-api-handler" }
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.orders.arn
  function_name    = aws_lambda_function.processor.arn
  batch_size       = 10
  enabled          = true
}

###############################################################################
# API Gateway
###############################################################################

resource "aws_api_gateway_rest_api" "main" {
  name        = "ministack-api"
  description = "MiniStack REST API"
  tags        = { Name = "ministack-api" }
}

resource "aws_api_gateway_resource" "items" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "items"
}

resource "aws_api_gateway_method" "items_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.items.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "items_get" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.items.id
  http_method             = aws_api_gateway_method.items_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

resource "aws_api_gateway_method" "items_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.items.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "items_post" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.items.id
  http_method             = aws_api_gateway_method.items_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.api_handler.invoke_arn
}

resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  depends_on  = [aws_api_gateway_integration.items_get, aws_api_gateway_integration.items_post]
}

resource "aws_api_gateway_stage" "dev" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "dev"
}

resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = "prod"
}

###############################################################################
# EventBridge
###############################################################################

resource "aws_cloudwatch_event_bus" "app" {
  name = "ministack-app"
  tags = { Name = "ministack-app" }
}

resource "aws_cloudwatch_event_rule" "every_minute" {
  name                = "ministack-every-minute"
  description         = "Fires every minute for heartbeat"
  schedule_expression = "rate(1 minute)"
  tags                = { Name = "ministack-every-minute" }
}

resource "aws_cloudwatch_event_target" "heartbeat_lambda" {
  rule      = aws_cloudwatch_event_rule.every_minute.name
  target_id = "LambdaProcessor"
  arn       = aws_lambda_function.processor.arn
}

resource "aws_cloudwatch_event_rule" "order_created" {
  name           = "ministack-order-created"
  description    = "Matches order.created events on app bus"
  event_bus_name = aws_cloudwatch_event_bus.app.name
  event_pattern = jsonencode({
    source      = ["ministack.orders"]
    detail-type = ["order.created"]
  })
  tags = { Name = "ministack-order-created" }
}

resource "aws_cloudwatch_event_target" "order_to_sqs" {
  rule           = aws_cloudwatch_event_rule.order_created.name
  event_bus_name = aws_cloudwatch_event_bus.app.name
  target_id      = "OrdersQueue"
  arn            = aws_sqs_queue.orders.arn
}

###############################################################################
# Glue
###############################################################################

resource "aws_glue_catalog_database" "raw" {
  name        = "ministack_raw"
  description = "Raw ingested data"
}

resource "aws_glue_catalog_database" "curated" {
  name        = "ministack_curated"
  description = "Curated / transformed data"
}

resource "aws_glue_catalog_table" "events" {
  name          = "events"
  database_name = aws_glue_catalog_database.raw.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification" = "json"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.raw.id}/events/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "json"
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
    }

    columns {
      name = "id"
      type = "string"
    }
    columns {
      name = "type"
      type = "string"
    }
    columns {
      name = "ts"
      type = "string"
    }
  }
}

resource "aws_glue_catalog_table" "users_csv" {
  name          = "users"
  database_name = aws_glue_catalog_database.raw.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    "classification"          = "csv"
    "skip.header.line.count"  = "1"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.raw.id}/exports/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "csv"
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
      parameters            = { "field.delim" = "," }
    }

    columns {
      name = "id"
      type = "int"
    }
    columns {
      name = "name"
      type = "string"
    }
    columns {
      name = "email"
      type = "string"
    }
    columns {
      name = "role"
      type = "string"
    }
    columns {
      name = "created_at"
      type = "string"
    }
  }
}

resource "aws_glue_job" "etl" {
  name     = "ministack-etl"
  role_arn = aws_iam_role.glue_service.arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.glue_scripts.id}/scripts/etl_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"   = "python"
    "--TempDir"        = "s3://${aws_s3_bucket.glue_scripts.id}/tmp/"
    "--enable-metrics" = "true"
    "--SOURCE_BUCKET"  = aws_s3_bucket.raw.id
    "--DEST_BUCKET"    = aws_s3_bucket.processed.id
  }

  max_retries       = 1
  number_of_workers = 2
  worker_type       = "G.1X"
  glue_version      = "4.0"

  tags = { Name = "ministack-etl" }
}

resource "aws_glue_crawler" "raw_events" {
  name          = "ministack-raw-events"
  role          = aws_iam_role.glue_service.arn
  database_name = aws_glue_catalog_database.raw.name

  s3_target {
    path = "s3://${aws_s3_bucket.raw.id}/events/"
  }

  tags = { Name = "ministack-raw-events" }
}

###############################################################################
# Step Functions
###############################################################################

resource "aws_sfn_state_machine" "order_pipeline" {
  name     = "ministack-order-pipeline"
  role_arn = aws_iam_role.sfn_exec.arn

  definition = jsonencode({
    Comment = "MiniStack order processing pipeline"
    StartAt = "ValidateOrder"
    States = {
      ValidateOrder = {
        Type     = "Task"
        Resource = aws_lambda_function.processor.arn
        Next     = "ProcessPayment"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "OrderFailed"
        }]
      }
      ProcessPayment = {
        Type     = "Task"
        Resource = aws_lambda_function.processor.arn
        Next     = "FulfillOrder"
      }
      FulfillOrder = {
        Type     = "Task"
        Resource = aws_lambda_function.processor.arn
        Next     = "NotifyCustomer"
      }
      NotifyCustomer = {
        Type     = "Task"
        Resource = aws_lambda_function.processor.arn
        End      = true
      }
      OrderFailed = {
        Type  = "Fail"
        Error = "OrderProcessingFailed"
        Cause = "An error occurred during order processing"
      }
    }
  })

  tags = { Name = "ministack-order-pipeline" }
}

resource "aws_sfn_state_machine" "data_quality" {
  name     = "ministack-data-quality"
  role_arn = aws_iam_role.sfn_exec.arn

  definition = jsonencode({
    Comment = "MiniStack data quality check"
    StartAt = "CheckSchema"
    States = {
      CheckSchema = {
        Type     = "Task"
        Resource = aws_lambda_function.processor.arn
        Next     = "CheckVolume"
      }
      CheckVolume = {
        Type = "Choice"
        Choices = [{
          Variable           = "$.recordCount"
          NumericGreaterThan = 0
          Next               = "PassQuality"
        }]
        Default = "FailQuality"
      }
      PassQuality = {
        Type = "Succeed"
      }
      FailQuality = {
        Type  = "Fail"
        Error = "DataQualityFailed"
        Cause = "Record count is zero"
      }
    }
  })

  tags = { Name = "ministack-data-quality" }
}

###############################################################################
# WAF
###############################################################################

resource "aws_wafv2_ip_set" "blocked_ips" {
  name               = "ministack-blocked-ips"
  scope              = "REGIONAL"
  ip_address_version = "IPV4"
  addresses          = ["192.168.100.0/24", "10.99.0.0/16"]
  tags               = { Name = "ministack-blocked-ips" }
}

resource "aws_wafv2_web_acl" "main" {
  name  = "ministack-web-acl"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "BlockBadIPs"
    priority = 1

    action {
      block {}
    }

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.blocked_ips.arn
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "BlockBadIPs"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimitRule"
    priority = 2

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "ministack-web-acl"
    sampled_requests_enabled   = true
  }

  tags = { Name = "ministack-web-acl" }
}

###############################################################################
# Outputs
###############################################################################

output "vpc_id"                { value = aws_vpc.main.id }
output "s3_raw_bucket"         { value = aws_s3_bucket.raw.id }
output "s3_processed_bucket"   { value = aws_s3_bucket.processed.id }
output "s3_firehose_bucket"    { value = aws_s3_bucket.firehose_dest.id }
output "dynamodb_users_table"  { value = aws_dynamodb_table.users.id }
output "dynamodb_events_table" { value = aws_dynamodb_table.events.id }
output "dynamodb_orders_table" { value = aws_dynamodb_table.orders.id }
output "sqs_orders_url"        { value = aws_sqs_queue.orders.id }
output "sqs_notifications_url" { value = aws_sqs_queue.notifications.id }
output "sns_alerts_arn"        { value = aws_sns_topic.alerts.arn }
output "sns_events_arn"        { value = aws_sns_topic.events.arn }
output "kinesis_stream_events" { value = aws_kinesis_stream.events.name }
output "kinesis_stream_click"  { value = aws_kinesis_stream.clickstream.name }
output "firehose_stream"       { value = aws_kinesis_firehose_delivery_stream.s3_delivery.name }
output "lambda_processor"      { value = aws_lambda_function.processor.function_name }
output "lambda_api_handler"    { value = aws_lambda_function.api_handler.function_name }
output "api_gateway_id"        { value = aws_api_gateway_rest_api.main.id }
output "kms_main_key_id"       { value = aws_kms_key.main.key_id }
output "sfn_order_pipeline"    { value = aws_sfn_state_machine.order_pipeline.id }
output "glue_etl_job"          { value = aws_glue_job.etl.name }
output "waf_web_acl_arn"       { value = aws_wafv2_web_acl.main.arn }
