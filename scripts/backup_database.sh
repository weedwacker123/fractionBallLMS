#!/bin/bash

# PostgreSQL Database Backup Script for Fraction Ball LMS
# Usage: ./scripts/backup_database.sh [environment]
# Environment: local, staging, production (default: local)

set -e  # Exit on any error

# Configuration
ENVIRONMENT=${1:-local}
BACKUP_DIR="/backups/postgresql"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=30

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

# Backup configuration
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${ENVIRONMENT}_${TIMESTAMP}.sql.gz"
BACKUP_LOG="${BACKUP_DIR}/backup_${ENVIRONMENT}.log"

echo "🗄️  Starting PostgreSQL backup for ${ENVIRONMENT} environment..."
echo "Database: ${DB_NAME}@${DB_HOST}:${DB_PORT}"
echo "Backup file: ${BACKUP_FILE}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Perform backup with compression
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting backup..." >> "${BACKUP_LOG}"

if PGPASSWORD="${DATABASE_PASSWORD}" pg_dump \
    --host="${DB_HOST}" \
    --port="${DB_PORT}" \
    --username="${DB_USER}" \
    --dbname="${DB_NAME}" \
    --verbose \
    --clean \
    --if-exists \
    --create \
    --format=custom \
    --no-owner \
    --no-privileges | gzip > "${BACKUP_FILE}"; then
    
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup completed successfully. Size: ${BACKUP_SIZE}" >> "${BACKUP_LOG}"
    echo "✅ Backup completed successfully!"
    echo "📁 Backup file: ${BACKUP_FILE} (${BACKUP_SIZE})"
    
    # Verify backup integrity
    echo "🔍 Verifying backup integrity..."
    if gunzip -t "${BACKUP_FILE}"; then
        echo "✅ Backup integrity verified"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup integrity verified" >> "${BACKUP_LOG}"
    else
        echo "❌ Backup integrity check failed!"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Backup integrity check failed" >> "${BACKUP_LOG}"
        exit 1
    fi
    
else
    echo "❌ Backup failed!"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Backup failed" >> "${BACKUP_LOG}"
    exit 1
fi

# Clean up old backups
echo "🧹 Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find "${BACKUP_DIR}" -name "${DB_NAME}_${ENVIRONMENT}_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
CLEANED_COUNT=$(find "${BACKUP_DIR}" -name "${DB_NAME}_${ENVIRONMENT}_*.sql.gz" -type f -mtime +${RETENTION_DAYS} | wc -l)

if [ ${CLEANED_COUNT} -gt 0 ]; then
    echo "🗑️  Cleaned up ${CLEANED_COUNT} old backup files"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Cleaned up ${CLEANED_COUNT} old backups" >> "${BACKUP_LOG}"
fi

# Upload to cloud storage (optional)
if [ -n "${BACKUP_CLOUD_BUCKET}" ]; then
    echo "☁️  Uploading backup to cloud storage..."
    
    if command -v gsutil &> /dev/null; then
        # Google Cloud Storage
        if gsutil cp "${BACKUP_FILE}" "gs://${BACKUP_CLOUD_BUCKET}/database/"; then
            echo "✅ Backup uploaded to Google Cloud Storage"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup uploaded to GCS" >> "${BACKUP_LOG}"
        else
            echo "⚠️  Failed to upload backup to Google Cloud Storage"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: GCS upload failed" >> "${BACKUP_LOG}"
        fi
    elif command -v aws &> /dev/null; then
        # AWS S3
        if aws s3 cp "${BACKUP_FILE}" "s3://${BACKUP_CLOUD_BUCKET}/database/"; then
            echo "✅ Backup uploaded to AWS S3"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup uploaded to S3" >> "${BACKUP_LOG}"
        else
            echo "⚠️  Failed to upload backup to AWS S3"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: S3 upload failed" >> "${BACKUP_LOG}"
        fi
    fi
fi

# Send notification (optional)
if [ -n "${SLACK_WEBHOOK_URL}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"✅ Database backup completed for ${ENVIRONMENT}\n📁 Size: ${BACKUP_SIZE}\n🕐 Time: $(date)\"}" \
        "${SLACK_WEBHOOK_URL}" || echo "⚠️  Failed to send Slack notification"
fi

echo "🎉 Database backup process completed!"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Backup process completed" >> "${BACKUP_LOG}"










