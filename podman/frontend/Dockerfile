FROM node:20-slim as builder

WORKDIR /app
COPY . .

RUN corepack enable && \
    yarn install && \
    cd src/legisweb_frontend && \
    yarn exec vite  build --emptyOutDir --outDir=/data


FROM caddy:2

COPY --from=builder /app/podman/frontend/etc/caddy /etc/caddy
COPY --from=builder /data /data