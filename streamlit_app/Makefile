.PHONY: install run stop localstack logs docker-build docker-run docker-stop help

IMAGE_NAME = ministack-ui-streamlit

help:
	@echo "Usage:"
	@echo "  make install        - Install Python dependencies"
	@echo "  make run            - Start Streamlit app locally"
	@echo "  make localstack     - Start LocalStack + Streamlit UI via docker compose"
	@echo "  make stop           - Stop all docker compose services"
	@echo "  make logs           - Show docker compose logs"
	@echo "  make docker-build   - Build Streamlit Docker image"
	@echo "  make docker-run     - Run Streamlit in Docker (standalone)"
	@echo "  make docker-stop    - Stop standalone Docker container"

install:
	source ../venv/bin/activate && \
	pip install -r requirements.txt

run:
	source ../venv/bin/activate && \
	streamlit run app.py

localstack:
	docker compose -f ../ministack-docker/docker-compose.yml up -d

stop:
	docker compose -f ../ministack-docker/docker-compose.yml down

logs:
	docker compose -f ../ministack-docker/docker-compose.yml logs -f

docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run: docker-build
	docker run -d \
		--name $(IMAGE_NAME) \
		-p 8501:8501 \
		-e LOCALSTACK_ENDPOINT=http://host.docker.internal:4566 \
		$(IMAGE_NAME)
	@echo "Streamlit UI running at http://localhost:8501"

docker-stop:
	docker stop $(IMAGE_NAME) && docker rm $(IMAGE_NAME)

