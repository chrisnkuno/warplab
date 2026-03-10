ARG CUDA_IMAGE=nvidia/cuda:12.4.1-devel-ubuntu24.04
FROM ${CUDA_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV PATH="/root/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    python3-pip \
    curl \
    git \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /workspace

COPY .python-version pyproject.toml uv.lock README.md CONTRIBUTING.md ./
COPY warplab ./warplab
COPY projects ./projects
COPY notebooks ./notebooks
COPY docs ./docs
COPY tests ./tests

RUN uv sync --dev --frozen

EXPOSE 8888

CMD ["uv", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
