# Week 2-3 Technical Infrastructure Guide

##  Docker Deployment

### Quick Start

```bash
# Build and run entire stack
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop all services
docker-compose down
```

### Access Points
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **TensorBoard**: http://localhost:6006
- **Dashboard**: http://localhost:8080

### Individual Service Management

```bash
# Build only the app
docker build -t power-grid-optimization .

# Run app only
docker run -p 8000:8000 power-grid-optimization

# Execute commands inside container
docker-compose exec app bash
docker-compose exec app pytest tests/ -v

# View resource usage
docker stats
```

---

##  REST API Usage

### Starting the API

**Option 1: Docker (recommended)**
```bash
docker-compose up app
```

**Option 2: Local**
```bash
# Install dependencies
pip install -r requirements.txt

# Run API server
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2024-01-14T15:00:00",
  "version": "1.0.0"
}
```

#### 2. Get Dispatch Prediction
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "current_demand": 750.5,
    "demand_forecast": [760, 770, 780, 790],
    "generator_outputs": [150, 180, 200, 120, 100],
    "hour_of_day": 14,
    "day_of_week": 2
  }'

# Response:
{
  "generator_adjustments": [0.12, -0.05, 0.08, -0.02, 0.03],
  "predicted_cost": 31500.0,
  "predicted_supply": 755.0,
  "confidence": 0.95,
  "timestamp": "2024-01-14T15:00:00"
}
```

#### 3. Load/Reload Model
```bash
curl -X POST http://localhost:8000/model/load

# Optional: specify model path
curl -X POST "http://localhost:8000/model/load?model_path=./models/best_model.zip"
```

#### 4. Model Information
```bash
curl http://localhost:8000/model/info

# Response:
{
  "loaded": true,
  "observation_space": "Box(-10.0, 10.0, (24,), float32)",
  "action_space": "Box(-1.0, 1.0, (5,), float32)",
  "num_generators": 5
}
```

#### 5. Prometheus Metrics
```bash
curl http://localhost:8000/metrics

# Returns Prometheus format metrics
```

### Interactive API Documentation

Visit http://localhost:8000/docs for:
- Interactive API testing
- Request/response schemas
- Try-it-out functionality

---

##  Prometheus Monitoring

### Accessing Prometheus

1. Open http://localhost:9090
2. Navigate to Graph tab
3. Try sample queries:

```promql
# Total API requests
api_requests_total

# Request rate (per second)
rate(api_requests_total[5m])

# Request latency percentiles
histogram_quantile(0.95, api_request_duration_seconds_bucket)

# Total predictions
predictions_total

# Model load time
model_load_seconds
```

### Configuring Alerts

Edit `monitoring/prometheus.yml`:

```yaml
rule_files:
  - "alerts/*.yml"

# Create alerts/high_latency.yml:
groups:
  - name: api_performance
    interval: 30s
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.95, api_request_duration_seconds_bucket) > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency detected"
```

---

##  Grafana Dashboards

### Initial Setup

1. Open http://localhost:3000
2. Login: admin/admin (change password)
3. Add Prometheus data source:
   - Configuration → Data Sources → Add
   - Type: Prometheus
   - URL: http://prometheus:9090
   - Save & Test

### Import Pre-built Dashboard

Create `monitoring/grafana/dashboards/api_dashboard.json`:

```json
{
  "dashboard": {
    "title": "Grid Optimization API",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(api_requests_total[5m])"
        }]
      },
      {
        "title": "Prediction Count",
        "targets": [{
          "expr": "predictions_total"
        }]
      }
    ]
  }
}
```

Import via: Dashboards → Import → Upload JSON

---

##  Testing

### Run All Tests with Coverage

```bash
# Local
pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Docker
docker-compose exec app pytest tests/ -v --cov=. --cov-report=html

# View HTML report
open htmlcov/index.html
```

### Run Specific Test Suites

```bash
# Environment tests only
pytest tests/test_environment.py -v

# Integration tests
pytest tests/test_integration.py -v

# With verbose output
pytest tests/ -vv -s
```

### Test Coverage Goals

Current target: **80%+**

Check coverage:
```bash
pytest --cov=. --cov-report=term-missing
```

Missing areas will be shown with line numbers.

---

##  Troubleshooting

### Docker Issues

**Problem**: Container won't start
```bash
# Check logs
docker-compose logs app

# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

**Problem**: Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process or change port in docker-compose.yml
```

### API Issues

**Problem**: Model not loading
```bash
# Check model file exists
ls -lh models/best_model.zip

# Try manual load
curl -X POST http://localhost:8000/model/load

# Check API logs
docker-compose logs -f app
```

**Problem**: High latency
```bash
# Check Prometheus metrics
curl http://localhost:8000/metrics | grep duration

# Monitor in Grafana
```

### Monitoring Issues

**Problem**: Prometheus not scraping
```bash
# Check Prometheus targets
http://localhost:9090/targets

# Verify app is exposing metrics
curl http://localhost:8000/metrics

# Check network connectivity
docker-compose exec prometheus ping app
```

---

##  Production Deployment

### Environment Variables

Create `.env` file:

```bash
# Application
ENVIRONMENT=production
LOG_LEVEL=WARNING
MODEL_PATH=/app/models/production_model.zip

# Database (if added)
DATABASE_URL=postgresql://user:pass@db:5432/grid_opt

# Security
API_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://yourdomain.com

# Monitoring
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
```

### Security Hardening

1. **Enable authentication**:
```python
# api/main.py
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/predict")
async def predict(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Validate token
    ...
```

2. **Rate limiting**:
```bash
pip install slowapi

# Add to api/main.py
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/predict")
@limiter.limit("10/minute")
async def predict(...):
    ...
```

3. **HTTPS only**:
```bash
# Use nginx or Caddy as reverse proxy
# docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
    - ./ssl:/etc/nginx/ssl
```

### Scaling

**Horizontal scaling**:
```yaml
# docker-compose.yml
app:
  deploy:
    replicas: 3
```

**Load balancer** (nginx config):
```nginx
upstream api_backend {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}
```

---

##  Maintenance

### Regular Tasks

**Daily**:
- Check Grafana dashboards
- Review error logs: `docker-compose logs app | grep ERROR`

**Weekly**:
- Review Prometheus alerts
- Check disk usage: `docker system df`
- Prune old containers: `docker system prune -a`

**Monthly**:
- Update dependencies: `pip list --outdated`
- Retrain model if needed
- Review and optimize queries

### Backup

```bash
# Backup models
tar -czf models-backup-$(date +%Y%m%d).tar.gz models/

# Backup Prometheus data
docker-compose exec prometheus tar -czf /tmp/prometheus-backup.tar.gz /prometheus
docker cp $(docker-compose ps -q prometheus):/tmp/prometheus-backup.tar.gz .
```

---

##  Performance Benchmarks

### Expected Performance

| Metric | Target | Current |
|--------|--------|---------|
| API Latency (p95) | <100ms | ~50ms |
| Throughput | >100 req/s | ~150 req/s |
| Model Inference | <10ms | ~5ms |
| Memory Usage | <512MB | ~300MB |

### Load Testing

```bash
# Install Apache Bench
brew install apache-bench  # Mac
apt-get install apache2-utils  # Linux

# Test API
ab -n 1000 -c 10 -T 'application/json' -p request.json http://localhost:8000/predict

# request.json:
{
  "current_demand": 750,
  "demand_forecast": [760, 770, 780, 790],
  "generator_outputs": [150, 180, 200, 120, 100],
  "hour_of_day": 14,
  "day_of_week": 2
}
```

---

##  Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Prometheus Guide**: https://prometheus.io/docs/introduction/overview/
- **Grafana Tutorials**: https://grafana.com/tutorials/
- **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/

---

## ✅ Checklist for Production

- [ ] All tests passing (80%+ coverage)
- [ ] Docker images built and tagged
- [ ] Environment variables configured
- [ ] Prometheus scraping successfully
- [ ] Grafana dashboards created
- [ ] API authentication enabled
- [ ] Rate limiting configured
- [ ] HTTPS/TLS certificates installed
- [ ] Backup strategy in place
- [ ] Monitoring alerts configured
- [ ] Load testing completed
- [ ] Documentation updated

---

**Created**: Week 2-3 Technical Infrastructure  
**Version**: 1.0.0  
**Last Updated**: January 2024
