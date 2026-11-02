FROM python:3.13-slim
ARG SOURCE_COMMIT
LABEL org.opencontainers.image.revision=$SOURCE_COMMIT
WORKDIR /opt/pac
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements-lock.txt pyproject.toml ./
RUN --mount=type=secret,id=ca_bundle \
    if [ -f /run/secrets/ca_bundle ]; then export PIP_CERT=/run/secrets/ca_bundle; fi; \
    python -m pip install --no-cache-dir -r requirements-lock.txt
COPY app ./app
COPY scripts ./scripts
COPY db ./db
COPY evaluation ./evaluation
COPY training ./training
RUN python -m pip check
COPY runtime_entrypoint.py ./runtime_entrypoint.py
RUN chmod -R a+rX /opt/pac
ENV PYTHONPATH=/opt/pac
ENTRYPOINT ["python", "/opt/pac/runtime_entrypoint.py"]
