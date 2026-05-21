# MiniStack Infrastructure

Two ways to populate all 17 services in LocalStack:

| Method         | File                | How                                          |
|----------------|---------------------|----------------------------------------------|
| **Terraform**  | `terraform/main.tf` | Declarative, idempotent, tracks state        |
| **Shell seed** | `scripts/seed.sh`   | Direct AWS CLI calls, fastest for dev resets |

---

## Prerequisites

```bash
# LocalStack running
docker run --rm -d -p 4566:4566 localstack/localstack

# Terraform
brew install terraform        # or https://developer.hashicorp.com/terraform/install

# AWS CLI + local alias
brew install awscli
alias awslocal='aws --endpoint-url=http://localhost:4566 --region us-east-1 \
  --no-cli-pager'
```

---

## Option A – Terraform

```bash
cd terraform

# First run
terraform init
terraform apply -auto-approve

# View what was created
terraform output

# Tear down
terraform destroy -auto-approve
```

### What Terraform creates

| Service            | Resources                                                                  |
|--------------------|----------------------------------------------------------------------------|
| **KMS**            | 2 keys (`ministack-main`, `ministack-s3`) + aliases                        |
| **IAM**            | 4 roles (lambda, glue, sfn, firehose), 1 policy, 2 users                   |
| **VPC**            | VPC `10.0.0.0/16`, 3 subnets, IGW, route table, 2 SGs                      |
| **EC2**            | 2 instances (`ministack-web` t3.micro, `ministack-worker` t3.small)        |
| **S3**             | 4 buckets + sample JSON / CSV / Glue script objects                        |
| **DynamoDB**       | 3 tables (`users`, `events`, `orders`) + seed items                        |
| **SQS**            | 4 queues (orders + DLQ, notifications, tasks.fifo)                         |
| **SNS**            | 2 topics (alerts, events) + SQS subscription                               |
| **CloudWatch**     | 3 log groups, 1 stream, 2 metric alarms                                    |
| **Kinesis**        | 2 streams (`ministack-events` 2-shard, `ministack-clickstream` 1-shard)    |
| **Firehose**       | 1 delivery stream → S3 with GZIP, partitioned prefix                       |
| **Lambda**         | 2 functions (`ministack-processor`, `ministack-api-handler`) + SQS trigger |
| **API Gateway**    | 1 REST API, `/items` GET+POST → Lambda, `dev` + `prod` stages              |
| **EventBridge**    | 1 custom bus, 2 rules (schedule + event pattern), 2 targets                |
| **Glue**           | 2 databases, 2 catalog tables (JSON + CSV), 1 ETL job, 1 crawler           |
| **Step Functions** | 2 state machines (`order-pipeline`, `data-quality`)                        |
| **WAF**            | 1 IP set (blocked CIDRs), 1 Web ACL (block + rate-limit rules)             |

---

## Option B – Shell seed

```bash
chmod +x scripts/seed.sh

# Seed all services
./scripts/seed.sh

# Wipe S3 buckets and re-seed everything
./scripts/seed.sh --clean

# Watch progress live
tail -f seed.log
```

The script creates the same resources as Terraform but uses raw AWS CLI calls. Safe to re-run — most commands gracefully skip already-existing resources. A summary table is printed at the end.

---

## Verify everything is visible in the UI

```bash
# Quick smoke-test — list one resource per service
awslocal kms          list-keys
awslocal iam          list-users
awslocal ec2          describe-instances    --query 'Reservations[*].Instances[*].Tags'
awslocal s3           ls
awslocal dynamodb     list-tables
awslocal sqs          list-queues
awslocal sns          list-topics
awslocal logs         describe-log-groups
awslocal kinesis      list-streams
awslocal lambda       list-functions
awslocal firehose     list-delivery-streams
awslocal apigateway   get-rest-apis
awslocal events       list-rules
awslocal glue         get-databases
awslocal stepfunctions list-state-machines
awslocal wafv2        list-web-acls --scope REGIONAL
awslocal kms          list-aliases
```

---

## Notes

- Both approaches target `http://localhost:4566` with `access_key=test / secret_key=test`.  
- Terraform stores state in `terraform/terraform.tfstate` — do not commit to VCS.  
- LocalStack free tier supports all these services; some WAF / Glue features may need LocalStack Pro.
