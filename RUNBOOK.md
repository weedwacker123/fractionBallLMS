# Fraction Ball LMS Operations Runbook

## Table of Contents
1. [System Overview](#system-overview)
2. [Environment Management](#environment-management)
3. [Deployment Procedures](#deployment-procedures)
4. [Database Operations](#database-operations)
5. [Backup & Recovery](#backup--recovery)
6. [Monitoring & Alerting](#monitoring--alerting)
7. [Troubleshooting](#troubleshooting)
8. [Scaling Operations](#scaling-operations)
9. [Security Procedures](#security-procedures)
10. [Emergency Procedures](#emergency-procedures)

## System Overview

### Architecture
- **Backend:** Django 5.1 + Django REST Framework
- **Database:** PostgreSQL 16
- **Cache:** Redis 7
- **Authentication:** Firebase Auth with JWT verification
- **Storage:** Firebase Storage with CDN
- **Queue:** Redis Queue (RQ) for background jobs
- **Monitoring:** Custom health checks + external monitoring

### Key Components
- **Web Application:** Django app serving API and basic UI
- **Database:** PostgreSQL with optimized indexes
- **Cache Layer:** Redis for session storage and caching
- **File Storage:** Firebase Storage for videos and resources
- **Background Jobs:** RQ for bulk uploads and analytics

## Environment Management

### Environments
1. **Local Development**
   - Docker Compose setup
   - Local PostgreSQL and Redis
   - Firebase Emulator (optional)

2. **Staging**
   - Production-like environment
   - Separate Firebase project
   - Automated deployments from main branch

3. **Production**
   - High availability setup
   - Production Firebase project
   - Manual deployment approval required

### Environment Variables

#### Required for All Environments
```bash
SECRET_KEY=<django-secret-key>
DEBUG=false
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgres://user:pass@host:port/dbname

# Redis
REDIS_URL=redis://host:port/0

# Firebase
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
FIREBASE_STORAGE_BUCKET=your-project-default-appspot.com
```

#### Production-Specific
```bash
# Security
SECURE_SSL_REDIRECT=true
SESSION_COOKIE_SECURE=true
CSRF_COOKIE_SECURE=true
SECURE_HSTS_SECONDS=31536000

# Performance
THROTTLE_ANON=100/hour
THROTTLE_USER=1000/hour
THROTTLE_LIBRARY=500/hour

# Monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
ALERT_EMAIL_FROM=alerts@yourdomain.com
ALERT_EMAIL_TO=admin@yourdomain.com,ops@yourdomain.com
```

## Deployment Procedures

### Pre-Deployment Checklist
1. [ ] All tests passing
2. [ ] QA checklist completed
3. [ ] Database migrations reviewed
4. [ ] Environment variables updated
5. [ ] Backup created
6. [ ] Rollback plan prepared

### Deployment Steps

#### Staging Deployment
```bash
# 1. Pull latest code
git checkout main
git pull origin main

# 2. Build and deploy
docker-compose -f docker-compose.staging.yml build
docker-compose -f docker-compose.staging.yml down
docker-compose -f docker-compose.staging.yml up -d

# 3. Run migrations
make migrate-staging

# 4. Verify deployment
curl https://staging.yourdomain.com/api/healthz/
```

#### Production Deployment
```bash
# 1. Create backup
./scripts/backup_database.sh production

# 2. Deploy with zero downtime
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d --no-deps web
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# 3. Health check
./scripts/health_monitor.py --config production.json

# 4. Verify critical functions
curl -H "Authorization: Bearer <token>" https://yourdomain.com/api/me/
```

### Rollback Procedure
```bash
# 1. Stop current version
docker-compose -f docker-compose.prod.yml down

# 2. Restore database if needed
./scripts/restore_database.sh /backups/pre_deploy_backup.sql.gz production

# 3. Deploy previous version
git checkout <previous-tag>
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# 4. Verify rollback
curl https://yourdomain.com/api/healthz/
```

## Database Operations

### Daily Operations
```bash
# Check database status
make db-status

# View slow queries
make db-slow-queries

# Update table statistics
make db-analyze
```

### Migrations
```bash
# Create migration
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Check migration status
docker-compose exec web python manage.py showmigrations
```

### Performance Monitoring
```bash
# Check database size
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check index usage
SELECT 
    indexrelname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes 
ORDER BY idx_scan DESC;

# Monitor connections
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
```

## Backup & Recovery

### Automated Backups
- **Schedule:** Daily at 2 AM UTC
- **Retention:** 30 days local, 90 days cloud
- **Location:** `/backups/postgresql/`
- **Monitoring:** Backup status checked by health monitor

### Manual Backup
```bash
# Create backup
./scripts/backup_database.sh production

# Verify backup
gunzip -t /backups/postgresql/latest_backup.sql.gz
```

### Recovery Procedures

#### Database Recovery
```bash
# 1. Stop application
docker-compose -f docker-compose.prod.yml stop web

# 2. Restore database
./scripts/restore_database.sh /backups/backup_file.sql.gz production

# 3. Restart application
docker-compose -f docker-compose.prod.yml start web

# 4. Verify recovery
./scripts/health_monitor.py
```

#### File Storage Recovery
```bash
# Firebase Storage has built-in redundancy
# For additional backup, sync to secondary storage:
gsutil -m rsync -r gs://your-bucket gs://backup-bucket
```

## Monitoring & Alerting

### Health Checks
```bash
# Manual health check
./scripts/health_monitor.py --verbose

# Automated monitoring (cron)
*/5 * * * * /path/to/scripts/health_monitor.py --config /path/to/monitor.json
```

### Key Metrics to Monitor
1. **Response Times**
   - API endpoints < 2s average
   - Dashboard < 3s p95
   - Library browsing < 1s p95

2. **Error Rates**
   - HTTP 5xx errors < 1%
   - Authentication failures < 5%
   - Upload failures < 2%

3. **System Resources**
   - CPU usage < 70%
   - Memory usage < 80%
   - Disk usage < 85%
   - Database connections < 80% of max

4. **Business Metrics**
   - Daily active users
   - Content upload success rate
   - Video streaming success rate

### Alert Thresholds
- **Critical:** System down, database unreachable, disk > 95%
- **Warning:** High response times, elevated error rates, resources > 80%
- **Info:** Deployment completed, backup finished

## Troubleshooting

### Common Issues

#### High Response Times
```bash
# 1. Check database performance
docker-compose exec db psql -U postgres -d fractionball -c "
SELECT query, total_time, calls, mean_time 
FROM pg_stat_statements 
WHERE mean_time > 1000 
ORDER BY mean_time DESC LIMIT 10;"

# 2. Check cache hit rates
docker-compose exec redis redis-cli info stats

# 3. Check system resources
docker stats
```

#### Database Connection Issues
```bash
# Check connection count
docker-compose exec db psql -U postgres -c "
SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Check for locks
docker-compose exec db psql -U postgres -c "
SELECT * FROM pg_stat_activity WHERE waiting = true;"

# Restart database (last resort)
docker-compose restart db
```

#### Upload Failures
```bash
# Check Firebase credentials
docker-compose exec web python manage.py shell -c "
import firebase_admin
app = firebase_admin.get_app()
print(f'App: {app.name}, Project: {app.project_id}')
"

# Check storage permissions
# Review Firebase Storage rules in console

# Check disk space
df -h
```

#### Memory Issues
```bash
# Check memory usage by container
docker stats --no-stream

# Check Django memory usage
docker-compose exec web python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB')
"

# Restart application
docker-compose restart web
```

### Log Analysis
```bash
# Application logs
docker-compose logs -f web

# Database logs
docker-compose logs -f db

# Redis logs
docker-compose logs -f redis

# Filter for errors
docker-compose logs web | grep ERROR

# Search for specific issues
docker-compose logs web | grep "500\|Exception\|Error"
```

## Scaling Operations

### Vertical Scaling
```yaml
# docker-compose.prod.yml
services:
  web:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          memory: 2G
  
  db:
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G
```

### Horizontal Scaling
```yaml
# Load balancer setup
services:
  web:
    deploy:
      replicas: 3
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
```

### Database Scaling
- **Read Replicas:** For read-heavy workloads
- **Connection Pooling:** PgBouncer for connection management
- **Partitioning:** For large tables (audit logs, analytics)

## Security Procedures

### Security Updates
```bash
# Update base images
docker-compose pull

# Update Python dependencies
pip-compile requirements.in
docker-compose build --no-cache

# Update system packages
docker-compose exec web apt update && apt upgrade
```

### Access Management
```bash
# Rotate Firebase credentials
# 1. Generate new service account key
# 2. Update FIREBASE_CREDENTIALS_PATH
# 3. Restart application
# 4. Delete old key

# Update database passwords
# 1. Create new database user
# 2. Update DATABASE_URL
# 3. Test connection
# 4. Remove old user
```

### Security Monitoring
```bash
# Check for failed authentication attempts
docker-compose exec web python manage.py shell -c "
from content.models import AuditLog
failed_logins = AuditLog.objects.filter(
    action='LOGIN_FAILED',
    created_at__gte=timezone.now() - timedelta(hours=24)
).count()
print(f'Failed logins (24h): {failed_logins}')
"

# Monitor suspicious activity
grep "429\|403\|401" /var/log/nginx/access.log | tail -100
```

## Emergency Procedures

### System Down
1. **Immediate Response**
   ```bash
   # Check system status
   docker-compose ps
   
   # Check logs for errors
   docker-compose logs --tail=100
   
   # Restart services if needed
   docker-compose restart
   ```

2. **Communication**
   - Notify stakeholders via Slack/email
   - Update status page if available
   - Provide regular updates

3. **Recovery**
   - Identify root cause
   - Apply fix or rollback
   - Verify system functionality
   - Post-incident review

### Data Breach Response
1. **Immediate Actions**
   - Isolate affected systems
   - Change all passwords and API keys
   - Review access logs
   - Notify security team

2. **Investigation**
   - Preserve evidence
   - Analyze breach scope
   - Document timeline
   - Identify vulnerabilities

3. **Recovery**
   - Apply security patches
   - Restore from clean backups
   - Implement additional monitoring
   - User notification if required

### Performance Degradation
1. **Quick Wins**
   ```bash
   # Clear cache
   docker-compose exec redis redis-cli flushall
   
   # Restart application
   docker-compose restart web
   
   # Check resource usage
   docker stats
   ```

2. **Analysis**
   - Review slow query logs
   - Check system metrics
   - Analyze traffic patterns
   - Identify bottlenecks

3. **Mitigation**
   - Scale resources if needed
   - Optimize slow queries
   - Implement caching
   - Load balance if necessary

## Maintenance Windows

### Scheduled Maintenance
- **Frequency:** Monthly, first Sunday 2-4 AM UTC
- **Duration:** 2 hours maximum
- **Notification:** 48 hours advance notice

### Maintenance Tasks
```bash
# 1. System updates
docker-compose pull
docker-compose build --no-cache

# 2. Database maintenance
docker-compose exec db psql -U postgres -c "VACUUM ANALYZE;"
docker-compose exec db psql -U postgres -c "REINDEX DATABASE fractionball;"

# 3. Log rotation
find /var/log -name "*.log" -mtime +30 -delete

# 4. Cleanup old backups
find /backups -name "*.sql.gz" -mtime +30 -delete

# 5. Performance tuning
./scripts/optimize_database.sh
```

## Contact Information

### On-Call Rotation
- **Primary:** DevOps Team Lead
- **Secondary:** Senior Developer
- **Escalation:** CTO

### External Services
- **Firebase Support:** Firebase Console → Support
- **DNS Provider:** Contact provider support
- **Hosting Provider:** Platform-specific support

---

## Change Log
- **v1.0:** Initial runbook creation
- **v1.1:** Added security procedures
- **v1.2:** Enhanced troubleshooting section

**Last Updated:** December 2024  
**Next Review:** March 2025










