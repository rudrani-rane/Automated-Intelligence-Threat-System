# ATIS Production Deployment Guide

## Prerequisites
- Docker & Docker Compose installed
- PostgreSQL 15+
- Redis 7+
- Nginx (for production)
- SSL certificates (Let's Encrypt recommended)

## Deployment Steps

### 1. Clone Repository
```bash
git clone https://github.com/your-org/atis.git
cd atis
```

### 2. Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with your production values
```

**Critical: Change these values:**
- `SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- `POSTGRES_PASSWORD`: Strong password for PostgreSQL
- `REDIS_PASSWORD`: Strong password for Redis
- `JWT_SECRET_KEY`: Generate with same command as SECRET_KEY
- `NASA_API_KEY`: Get from https://api.nasa.gov/

### 3. Build and Start Services
```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 4. Initialize Database
```bash
# Database initialization runs automatically
# Check logs
docker-compose logs postgres

# Manual initialization (if needed)
docker-compose exec postgres psql -U atis_user -d atis -f /docker-entrypoint-initdb.d/init.sql
```

### 5. Verify Deployment
```bash
# Check application health
curl http://localhost:8000/

# Check WebSocket
# (Connect to ws://localhost:8000/api/ws)

# View logs
docker-compose logs -f app
```

### 6. Configure Nginx (Production)
```bash
# Copy nginx configuration
sudo cp nginx/nginx.conf /etc/nginx/sites-available/atis
sudo ln -s /etc/nginx/sites-available/atis /etc/nginx/sites-enabled/

# Install SSL certificate (Let's Encrypt)
sudo certbot --nginx -d your-domain.com

# Reload nginx
sudo systemctl reload nginx
```

### 7. Set Up Monitoring
```bash
# Access Grafana (optional)
http://localhost:3000
# Login: admin / <GRAFANA_PASSWORD from .env>

# Access Prometheus (optional)
http://localhost:9090
```

## Maintenance

### Backup Database
```bash
# Automated daily backups
docker-compose exec postgres pg_dump -U atis_user atis > backup_$(date +%Y%m%d).sql

# Restore from backup
docker-compose exec -T postgres psql -U atis_user atis < backup_20240101.sql
```

### Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose build app
docker-compose up -d app

# Check logs
docker-compose logs -f app
```

### Scale Workers
```bash
# Increase workers in docker-compose.yml
# Or use docker-compose scale
docker-compose up -d --scale app=4
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f redis
```

### Database Migrations
```bash
# Run migrations (when schema changes)
docker-compose exec app python -m alembic upgrade head
```

## Monitoring & Alerts

### Health Checks
- Application: `http://localhost:8000/`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

### Metrics to Monitor
- CPU/Memory usage
- WebSocket connections
- Database connections
- API response times
- Threat detection count

## Security Best Practices

1. **Change Default Passwords**: All default passwords in `.env.example`
2. **Use HTTPS**: Always use SSL/TLS in production
3. **Firewall Rules**: Only expose necessary ports (80, 443)
4. **Regular Updates**: Keep Docker images and dependencies updated
5. **Backup Strategy**: Automated daily backups with rotation
6. **Access Control**: Limit SSH access, use key-based auth
7. **Environment Variables**: Never commit `.env` to version control
8. **Secrets Management**: Use Docker secrets or vault for sensitive data

## Troubleshooting

### Application won't start
```bash
# Check logs
docker-compose logs app

# Check database connection
docker-compose exec app python -c "import psycopg2; print('DB OK')"
```

### WebSocket not connecting
- Check firewall allows WebSocket connections
- Verify nginx proxy settings for WebSocket
- Check browser console for errors

### High memory usage
- Reduce number of workers
- Implement Redis caching
- Check for memory leaks in logs

### Database slow queries
```bash
# Enable slow query log in PostgreSQL
# Check pg_stat_statements
docker-compose exec postgres psql -U atis_user -d atis -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

## Performance Tuning

### PostgreSQL
```sql
-- Increase connection pool
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

### Redis
```bash
# Increase max memory
docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Application
- Use gunicorn with 2-4 workers per CPU core
- Enable response compression
- Use CDN for static assets
- Implement query caching

## Support
- Documentation: `/docs` (Swagger UI)
- Issues: GitHub Issues
- Email: support@atis.local
