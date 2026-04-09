# ── Backend – FastAPI + uvicorn ──────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /workspace

# Cài dependencies trước để tận dụng layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
