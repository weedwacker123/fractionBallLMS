#!/bin/bash

# PostgreSQL Database Restore Script for Fraction Ball LMS
# Usage: ./scripts/restore_database.sh <backup_file> [environment]
# Example: ./scripts/restore_database.sh /backups/fractionball_production_20241201_120000.sql.gz staging

set -e  # Exit on any error

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <backup_file> [environment]"
    echo "Example: $0 /backups/fractionball_production_20241201_120000.sql.gz staging"
    exit 1
fi

BACKUP_FILE=$1
ENVIRONMENT=${2:-local}

# Configuration
RESTORE_LOG="/backups/restore_${ENVIRONMENT}.log"

# Validate backup file
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

# Load environment variables
if [ -f ".env.${ENVIRONMENT}" ]; then
    export $(cat .env.${ENVIRONMENT} | grep -v '^#' | xargs)
elif [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Database configuration
DB_NAME=${DATABASE_NAME:-fractionball}
DB_HOST=${DATABASE_HOST:-localhost}
DB_PORT=${DATABASE_PORT:-5432}
DB_USER=${DATABASE_USER:-postgres}

echo "🔄 Starting PostgreSQL restore for ${ENVIRONMENT} environment..."
echo "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
echo "Backup file: ${BACKUP_FILE}"
echo ""

# Safety confirmation for production
if [ "${ENVIRONMENT}" = "production" ]; then
    echo "⚠️  WARNING: You are about to restore to PRODUCTION environment!"
    echo "This will OVERWRITE the current production database."
    read -p "Are you absolutely sure you want to continue? (yes/no): " -r
    
    if [ "$REPLY" != "yes" ]; then
        echo "❌ Restore cancelled by user"
        exit 1
    fi
    
    echo "🔒 Production restore confirmed. Proceeding with caution..."
fi

# Start logging
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting restore from ${BACKUP_FILE}" >> "${RESTORE_LOG}"

# Verify backup file integrity
echo "🔍 Verifying backup file integrity..."
if gunzip -t "${BACKUP_FILE}"; then
    echo "✅ Backup file integrity verified"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup integrity verified" >> "${RESTORE_LOG}"
else
    echo "❌ Backup file is corrupted!"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Backup file corrupted" >> "${RESTORE_LOG}"
    exit 1
fi

# Create a pre-restore backup (safety measure)
if [ "${ENVIRONMENT}" != "local" ]; then
    echo "💾 Creating pre-restore backup as safety measure..."
    SAFETY_BACKUP="/backups/pre_restore_${DB_NAME}_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).sql.gz"
    
    if PGPASSWORD="${DATABASE_PASSWORD}" pg_dump \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --dbname="${DB_NAME}" \
        --format=custom \
        --no-owner \
        --no-privileges | gzip > "${SAFETY_BACKUP}"; then
        
        echo "✅ Safety backup created: ${SAFETY_BACKUP}"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Safety backup created" >> "${RESTORE_LOG}"
    else
        echo "⚠️  Failed to create safety backup, but continuing with restore..."
        echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: Safety backup failed" >> "${RESTORE_LOG}"
    fi
fi

# Stop application services (if running in Docker)
if command -v docker-compose &> /dev/null; then
    echo "⏸️  Stopping application services..."
    docker-compose stop web || echo "⚠️  Could not stop web service"
fi

# Perform restore
echo "🔄 Starting database restore..."

# Check if backup is in custom format or SQL format
if gunzip -t "${BACKUP_FILE}" 2>/dev/null; then
    # Compressed SQL format
    if gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${DATABASE_PASSWORD}" psql \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --dbname="${DB_NAME}" \
        --quiet; then
        restore_success=true
    else
        restore_success=false
    fi
else
    # Try pg_restore for custom format
    if PGPASSWORD="${DATABASE_PASSWORD}" pg_restore \
        --host="${DB_HOST}" \
        --port="${DB_PORT}" \
        --username="${DB_USER}" \
        --dbname="${DB_NAME}" \
        --clean \
        --if-exists \
        --no-owner \
        --no-privileges \
        --verbose \
        "${BACKUP_FILE}"; then
        restore_success=true
    else
        restore_success=false
    fi
fi

if [ "$restore_success" = true ]; then
    
    echo "✅ Database restore completed successfully!"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Restore completed successfully" >> "${RESTORE_LOG}"
    
else
    echo "❌ Database restore failed!"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Restore failed" >> "${RESTORE_LOG}"
    
    # Attempt to restore from safety backup if available
    if [ -f "${SAFETY_BACKUP}" ]; then
        echo "🚨 Attempting to restore from safety backup..."
        if gunzip -c "${SAFETY_BACKUP}" | PGPASSWORD="${DATABASE_PASSWORD}" psql \
            --host="${DB_HOST}" \
            --port="${DB_PORT}" \
            --username="${DB_USER}" \
            --dbname="${DB_NAME}" \
            --quiet; then
            
            echo "✅ Restored from safety backup"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Restored from safety backup" >> "${RESTORE_LOG}"
        else
            echo "❌ Safety backup restore also failed!"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Safety backup restore failed" >> "${RESTORE_LOG}"
        fi
    fi
    
    exit 1
fi

# Run migrations to ensure schema is up to date
echo "🔧 Running database migrations..."
if command -v docker-compose &> /dev/null; then
    docker-compose run --rm web python manage.py migrate || echo "⚠️  Migrations failed"
else
    python manage.py migrate || echo "⚠️  Migrations failed"
fi

# Restart application services
if command -v docker-compose &> /dev/null; then
    echo "▶️  Restarting application services..."
    docker-compose up -d web || echo "⚠️  Could not restart web service"
fi

# Verify restore
echo "🔍 Verifying restore..."
if PGPASSWORD="${DATABASE_PASSWORD}" psql \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --command="SELECT COUNT(*) FROM accounts_user;" > /dev/null 2>&1; then
    
    echo "✅ Restore verification passed"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Restore verification passed" >> "${RESTORE_LOG}"
else
    echo "❌ Restore verification failed!"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Restore verification failed" >> "${RESTORE_LOG}"
    exit 1
fi

# Send notification (optional)
if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Database restore completed for ${ENVIRONMENT}\n📁 From: $(basename ${BACKUP_FILE})\n🕐 Time: $(date)\"}" \
        "${SLACK_WEBHOOK_URL}" || echo "⚠️  Failed to send Slack notification"
fi

echo ""
echo "🎉 Database restore process completed successfully!"
echo "📊 Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
echo "📁 Restored from: ${BACKUP_FILE}"
echo "🕐 Completed at: $(date)"
echo ""

# Clean up safety backup if restore was successful
if [ -f "${SAFETY_BACKUP}" ] && [ "${ENVIRONMENT}" = "local" ]; then
    echo "🧹 Cleaning up safety backup for local environment..."
    rm -f "${SAFETY_BACKUP}"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - Restore process completed successfully" >> "${RESTORE_LOG}"
