# Streamlit UI for MiniStack

A simple Python-based interface for MiniStack using Streamlit.

---

## Features

- **Easy setup** with Python dependencies
- **Interactive widgets** for AWS services
- **Quick prototyping** with Streamlit
- **Docker support** for easy deployment

---

## Prerequisites

| Tool   | Version |
|--------|---------|
| Python | 3.11+   |
| Docker | 24+     |

---

## Getting Started

### 1. Install dependencies

```bash
cd streamlit_app
pip install -r requirements.txt
```

### 2. Start the Streamlit app

```bash
streamlit run app.py
```

The app will be available at: http://localhost:8501

---

## Project Structure

```
streamlit_app/
├── app.py                   # Main Streamlit app
├── aws_client.py            # AWS client configuration
├── pages_s3.py              # S3 page logic
├── pages_dynamo.py          # DynamoDB page logic
├── pages_sqs.py             # SQS page logic
├── pages_sns.py             # SNS page logic
├── pages_lambda.py          # Lambda page logic
├── pages_kinesis.py         # Kinesis page logic
├── pages_logs.py            # CloudWatch Logs page logic
├── pages_apigateway.py      # API Gateway page logic
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
└── Makefile                 # Helper commands
```

---

## Configuration

The AWS client is configured in `aws_client.py`:

```python
ENDPOINT = os.getenv("LOCALSTACK_ENDPOINT", "http://localhost:4566")
REGION = "us-east-1"
CREDENTIALS = dict(
    aws_access_key_id="test",
    aws_secret_access_key="test",
    region_name=REGION,
    endpoint_url=ENDPOINT,
)
```

---

## Docker

To run the Streamlit UI in Docker:

```bash
cd streamlit_app
docker build -t ministack-streamlit-ui .
docker run -p 8501:8501 -e LOCALSTACK_ENDPOINT=http://host.docker.internal:4566 ministack-streamlit-ui
```

---

## Docker Compose

A `docker-compose.yml` file is available in the `ministack-docker/` directory to run both MiniStack and the Streamlit UI together:

```bash
cd ministack-docker
docker-compose up
```

This will start:
- MiniStack on port 4566
- Streamlit UI on port 8501
- 