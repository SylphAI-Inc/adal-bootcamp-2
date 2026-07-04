# Container image for the Lumen demo BFF proxy: serves the storefront (site/)
# and proxies /api/* to AdaL Cloud with the Clerk JWT injected server-side.
#
# Build context is the example root (customer_sales_agent/) so the image can
# bundle proxy/, site/, and agent/ together:
#   docker build -f proxy/Dockerfile -t lumen-proxy .
FROM python:3.11-slim

WORKDIR /app

# Install proxy deps first (layer cache).
COPY proxy/requirements.txt ./proxy/requirements.txt
RUN pip install --no-cache-dir -r proxy/requirements.txt

# Bundle the proxy server, the static storefront, and the agent config.
COPY proxy/server.py ./proxy/server.py
COPY site/ ./site/
COPY agent/ ./agent/

# App Runner / ALB health checks and traffic hit 8080.
ENV HOST=0.0.0.0 PORT=8080
EXPOSE 8080

# ADAL_JWT must be provided at runtime (env var / secret) — never baked in.
WORKDIR /app/proxy
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
