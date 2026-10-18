# syntax=docker/dockerfile:1

# ---- Builder: install dependencies into a virtualenv ----
FROM python:3.14-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only requirements first so this layer is cached until dependencies change.
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- Runtime: slim image with the venv and app source only ----
FROM python:3.14-slim AS runtime

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION} \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /srv
COPY --from=builder /opt/venv /opt/venv
COPY app ./app

USER app
EXPOSE 8000

# python:3.12-slim has no curl, so use the standard library for the check.
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
