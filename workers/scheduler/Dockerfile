FROM python:3.12-slim
WORKDIR /app
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY apps/api/app ./app
COPY workers/shared ./workers/shared
COPY workers/scheduler/main.py ./main.py
CMD ["python", "main.py"]
