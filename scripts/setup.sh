#!/bin/bash
# Setup script untuk Anti-DDoS Stack
# Jalankan: chmod +x setup.sh && ./setup.sh

set -e

echo "🚀 Setup Anti-DDoS Stack Latest"

# Buat direktori log
mkdir -p logs/nginx

# Generate dummy SSL cert untuk development (optional)
if [ ! -f certs/localhost.crt ]; then
    mkdir -p certs
    openssl req -x509 -newkey rsa:4096 -keyout certs/localhost.key \
        -out certs/localhost.crt -days 365 -nodes \
        -subj "/CN=localhost" 2>/dev/null || true
fi

# Pull images
echo "📦 Pulling Docker images..."
docker-compose pull

# Build app
echo "🔨 Building app..."
docker-compose build app

# Start stack
echo "🚀 Starting stack..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services..."
sleep 10

# Check status
echo "📊 Service status:"
docker-compose ps

echo ""
echo "✅ Anti-DDoS Stack running!"
echo ""
echo "Endpoints:"
echo "  - Nginx:     http://localhost"
echo "  - App:       http://localhost/api/data"
echo "  - Health:    http://localhost/health"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana:   http://localhost:3000 (admin/admin)"
echo ""
echo "📝 Logs: docker-compose logs -f [service]"
echo "🛑 Stop:  docker-compose down"