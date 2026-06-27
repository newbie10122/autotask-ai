FROM python:3.12-slim
WORKDIR /app
COPY workers/shared ./workers/shared
COPY workers/autotask-sync/main.py ./main.py
CMD ["python", "main.py"]

