# Deployment (Nginx Reverse Proxy, cheese-style)

- Build from repo root (uses `src/deployment/.dockerignore`):  
  `docker build -t aimino-proxy:dev -f src/deployment/Dockerfile src/deployment`
- Run: `docker run --rm -p 80:80 aimino-proxy:dev`
- Upstream defaults to `host.docker.internal:8000` (see `nginx-conf/nginx/nginx.conf`); change to your API host.
- Entry: `docker-entrypoint.sh` now drives `nginx -g 'daemon off;'` (aligned with cheese-app-v3 style).

For production, layer TLS/k8s/compose as in cheese-app-v3 (proxy → api-service). 
