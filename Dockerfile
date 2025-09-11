FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates openssh-client python3 python3-pip tini \
 && rm -rf /var/lib/apt/lists/*

# Minimal deps; add your preferred Qwen runtime packages here
RUN pip3 install fastapi uvicorn[standard] pydantic==2.* \
    "gitpython>=3.1.40" "rich>=13.7" "xxhash>=3.4" "pyyaml>=6.0"

# Non-root for safer writes
RUN useradd -m -u 1000 surgeon
USER surgeon

WORKDIR /srv/surgeon
COPY app/ ./app/

# Harden at runtime with flags in compose (readOnlyRootFilesystem, no-new-privs)
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["python3","-m","uvicorn","app.api:app","--host","0.0.0.0","--port","8080"]
