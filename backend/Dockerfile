FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg libglib2.0-0 libgomp1 libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
COPY requirements-diarization.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG INSTALL_DIARIZATION=false
RUN if [ "$INSTALL_DIARIZATION" = "true" ]; then \
      pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu \
        torch==2.3.1+cpu torchaudio==2.3.1+cpu; \
      pip install --no-cache-dir -r requirements-diarization.txt; \
    fi

COPY app ./app
COPY tests ./tests

RUN mkdir -p /app/data /app/models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
