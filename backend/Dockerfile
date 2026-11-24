# EventZilla analytics API. Build from the repository root (it ships the data-science reports too):
#   docker build -f backend/Dockerfile -t twelvy1400/eventzilla-api .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 REPORTS_DIR=/srv/reports
WORKDIR /srv

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && useradd --system --uid 10001 api

COPY backend/app ./app
COPY ml/reports ./reports

USER api
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
