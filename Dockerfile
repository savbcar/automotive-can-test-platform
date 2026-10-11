FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir '.[dev]'
RUN cmake -S cpp -B cpp/build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build cpp/build --parallel \
    && ctest --test-dir cpp/build --output-on-failure
RUN pytest -q
RUN python -m automotive_can regression --output reports/docker

FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends can-utils iproute2 && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /app /app
COPY --from=builder /usr/local /usr/local
CMD ["python", "-m", "automotive_can", "demo"]
