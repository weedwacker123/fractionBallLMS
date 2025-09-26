#!/usr/bin/env python3
"""
Health monitoring script for Fraction Ball LMS

Performs comprehensive health checks and sends alerts when issues are detected.
Can be run as a cron job or standalone script.

Usage:
    python scripts/health_monitor.py [--config config.json] [--verbose]
"""

import argparse
import json
import logging
import os
import sys
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Add Django project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fractionball.settings')

import django
django.setup()

from django.core.cache import cache
from django.db import connection
from django.conf import settings


class HealthMonitor:
    """Comprehensive health monitoring for the LMS platform"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.base_url = config.get('base_url', 'http://localhost:8000')
        self.timeout = config.get('timeout', 30)
        self.alerts = []
        
        # Setup logging
        log_level = logging.DEBUG if config.get('verbose') else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def run_all_checks(self) -> Dict:
        """Run all health checks and return results"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'HEALTHY',
            'checks': {}
        }
        
        checks = [
            ('database', self.check_database),
            ('redis_cache', self.check_redis),
            ('api_endpoints', self.check_api_endpoints),
            ('firebase_storage', self.check_firebase_storage),
            ('disk_space', self.check_disk_space),
            ('memory_usage', self.check_memory_usage),
            ('response_times', self.check_response_times),
            ('error_rates', self.check_error_rates),
            ('background_jobs', self.check_background_jobs),
        ]
        
        for check_name, check_func in checks:
            try:
                self.logger.info(f"Running {check_name} check...")
                status, message, details = check_func()
                
                results['checks'][check_name] = {
                    'status': status,
                    'message': message,
                    'details': details,
                    'timestamp': datetime.now().isoformat()
                }
                
                if status != 'HEALTHY':
                    results['overall_status'] = 'UNHEALTHY'
                    self.alerts.append({
                        'check': check_name,
                        'status': status,
                        'message': message,
                        'details': details
                    })
                
            except Exception as e:
                self.logger.error(f"Check {check_name} failed with exception: {e}")
                results['checks'][check_name] = {
                    'status': 'ERROR',
                    'message': f"Check failed: {str(e)}",
                    'details': {},
                    'timestamp': datetime.now().isoformat()
                }
                results['overall_status'] = 'UNHEALTHY'
        
        return results
    
    def check_database(self) -> Tuple[str, str, Dict]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            # Check database size and table counts
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_tup_ins + n_tup_upd + n_tup_del as total_operations,
                        n_live_tup as live_tuples
                    FROM pg_stat_user_tables 
                    ORDER BY total_operations DESC 
                    LIMIT 5
                """)
                table_stats = cursor.fetchall()
            
            # Check for long-running queries
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM pg_stat_activity 
                    WHERE state = 'active' 
                    AND query_start < NOW() - INTERVAL '5 minutes'
                    AND query NOT LIKE '%pg_stat_activity%'
                """)
                long_queries = cursor.fetchone()[0]
            
            query_time = time.time() - start_time
            
            details = {
                'query_time_ms': round(query_time * 1000, 2),
                'table_stats': table_stats[:3],  # Top 3 most active tables
                'long_running_queries': long_queries
            }
            
            # Determine status
            if query_time > 5.0:
                return 'CRITICAL', f'Database query took {query_time:.2f}s', details
            elif query_time > 1.0:
                return 'WARNING', f'Database query took {query_time:.2f}s', details
            elif long_queries > 5:
                return 'WARNING', f'{long_queries} long-running queries detected', details
            else:
                return 'HEALTHY', 'Database is responsive', details
                
        except Exception as e:
            return 'CRITICAL', f'Database connection failed: {str(e)}', {}
    
    def check_redis(self) -> Tuple[str, str, Dict]:
        """Check Redis cache connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test basic connectivity
            cache.set('health_check', 'test_value', 60)
            retrieved_value = cache.get('health_check')
            
            if retrieved_value != 'test_value':
                return 'CRITICAL', 'Redis cache test failed', {}
            
            cache.delete('health_check')
            cache_time = time.time() - start_time
            
            # Get Redis info if available
            details = {
                'cache_time_ms': round(cache_time * 1000, 2),
                'backend': str(cache.__class__.__name__)
            }
            
            # Try to get Redis-specific stats
            try:
                from django_redis import get_redis_connection
                redis_conn = get_redis_connection("default")
                info = redis_conn.info()
                
                details.update({
                    'used_memory_mb': round(info.get('used_memory', 0) / 1024 / 1024, 2),
                    'connected_clients': info.get('connected_clients', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                })
                
                # Calculate hit rate
                hits = info.get('keyspace_hits', 0)
                misses = info.get('keyspace_misses', 0)
                if hits + misses > 0:
                    hit_rate = hits / (hits + misses)
                    details['hit_rate'] = round(hit_rate * 100, 2)
                
            except Exception:
                pass  # Redis-specific stats not available
            
            if cache_time > 1.0:
                return 'WARNING', f'Cache operation took {cache_time:.2f}s', details
            else:
                return 'HEALTHY', 'Redis cache is responsive', details
                
        except Exception as e:
            return 'CRITICAL', f'Redis connection failed: {str(e)}', {}
    
    def check_api_endpoints(self) -> Tuple[str, str, Dict]:
        """Check critical API endpoints"""
        endpoints = [
            '/api/healthz/',
            '/api/public-config/',
            '/api/library/videos/',
            '/api/dashboard/'
        ]
        
        results = {}
        total_time = 0
        failures = 0
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                
                headers = {}
                if endpoint not in ['/api/healthz/', '/api/public-config/']:
                    # These endpoints require authentication
                    headers['Authorization'] = 'Bearer test-token'
                
                response = requests.get(
                    f"{self.base_url}{endpoint}",
                    headers=headers,
                    timeout=self.timeout
                )
                
                response_time = time.time() - start_time
                total_time += response_time
                
                results[endpoint] = {
                    'status_code': response.status_code,
                    'response_time_ms': round(response_time * 1000, 2),
                    'success': response.status_code < 400
                }
                
                if response.status_code >= 400:
                    failures += 1
                    
            except requests.RequestException as e:
                results[endpoint] = {
                    'status_code': 0,
                    'response_time_ms': 0,
                    'success': False,
                    'error': str(e)
                }
                failures += 1
        
        avg_response_time = total_time / len(endpoints)
        
        details = {
            'endpoints_checked': len(endpoints),
            'failures': failures,
            'avg_response_time_ms': round(avg_response_time * 1000, 2),
            'results': results
        }
        
        if failures > len(endpoints) / 2:
            return 'CRITICAL', f'{failures}/{len(endpoints)} endpoints failing', details
        elif failures > 0:
            return 'WARNING', f'{failures}/{len(endpoints)} endpoints failing', details
        elif avg_response_time > 3.0:
            return 'WARNING', f'Average response time {avg_response_time:.2f}s', details
        else:
            return 'HEALTHY', 'All endpoints responding normally', details
    
    def check_firebase_storage(self) -> Tuple[str, str, Dict]:
        """Check Firebase Storage connectivity"""
        try:
            # This is a basic check - in production you'd test actual Firebase operations
            import firebase_admin
            from firebase_admin import storage
            
            # Try to initialize or get existing app
            try:
                app = firebase_admin.get_app()
            except ValueError:
                # App not initialized
                return 'WARNING', 'Firebase app not initialized', {}
            
            # Basic connectivity test would go here
            # For now, just check if the service is configured
            
            details = {
                'app_name': app.name,
                'project_id': app.project_id if hasattr(app, 'project_id') else 'unknown'
            }
            
            return 'HEALTHY', 'Firebase Storage configured', details
            
        except ImportError:
            return 'WARNING', 'Firebase Admin SDK not available', {}
        except Exception as e:
            return 'WARNING', f'Firebase check failed: {str(e)}', {}
    
    def check_disk_space(self) -> Tuple[str, str, Dict]:
        """Check available disk space"""
        try:
            import shutil
            
            # Check multiple mount points
            paths_to_check = ['/', '/tmp', '/var/log']
            if hasattr(settings, 'MEDIA_ROOT'):
                paths_to_check.append(settings.MEDIA_ROOT)
            
            results = {}
            min_free_percent = 100
            
            for path in paths_to_check:
                if os.path.exists(path):
                    total, used, free = shutil.disk_usage(path)
                    free_percent = (free / total) * 100
                    
                    results[path] = {
                        'total_gb': round(total / (1024**3), 2),
                        'used_gb': round(used / (1024**3), 2),
                        'free_gb': round(free / (1024**3), 2),
                        'free_percent': round(free_percent, 2)
                    }
                    
                    min_free_percent = min(min_free_percent, free_percent)
            
            details = {'disk_usage': results}
            
            if min_free_percent < 5:
                return 'CRITICAL', f'Disk space critically low: {min_free_percent:.1f}% free', details
            elif min_free_percent < 15:
                return 'WARNING', f'Disk space low: {min_free_percent:.1f}% free', details
            else:
                return 'HEALTHY', f'Disk space adequate: {min_free_percent:.1f}% free', details
                
        except Exception as e:
            return 'WARNING', f'Disk space check failed: {str(e)}', {}
    
    def check_memory_usage(self) -> Tuple[str, str, Dict]:
        """Check system memory usage"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            details = {
                'memory': {
                    'total_gb': round(memory.total / (1024**3), 2),
                    'used_gb': round(memory.used / (1024**3), 2),
                    'free_gb': round(memory.available / (1024**3), 2),
                    'percent_used': memory.percent
                },
                'swap': {
                    'total_gb': round(swap.total / (1024**3), 2),
                    'used_gb': round(swap.used / (1024**3), 2),
                    'percent_used': swap.percent
                }
            }
            
            if memory.percent > 90:
                return 'CRITICAL', f'Memory usage critical: {memory.percent:.1f}%', details
            elif memory.percent > 80:
                return 'WARNING', f'Memory usage high: {memory.percent:.1f}%', details
            else:
                return 'HEALTHY', f'Memory usage normal: {memory.percent:.1f}%', details
                
        except ImportError:
            return 'WARNING', 'psutil not available for memory monitoring', {}
        except Exception as e:
            return 'WARNING', f'Memory check failed: {str(e)}', {}
    
    def check_response_times(self) -> Tuple[str, str, Dict]:
        """Check recent response times from logs or metrics"""
        # This would typically integrate with your logging/metrics system
        # For now, return a placeholder
        
        details = {
            'note': 'Response time monitoring requires integration with logging system'
        }
        
        return 'HEALTHY', 'Response time monitoring not implemented', details
    
    def check_error_rates(self) -> Tuple[str, str, Dict]:
        """Check recent error rates"""
        try:
            # Check Django logs for recent errors (last hour)
            from content.models import AuditLog
            
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            # Count recent error-related audit logs
            error_actions = ['UPLOAD_FAILED', 'LOGIN_FAILED', 'SYSTEM_ERROR']
            recent_errors = AuditLog.objects.filter(
                created_at__gte=one_hour_ago,
                action__in=error_actions
            ).count()
            
            total_actions = AuditLog.objects.filter(
                created_at__gte=one_hour_ago
            ).count()
            
            error_rate = (recent_errors / max(total_actions, 1)) * 100
            
            details = {
                'recent_errors': recent_errors,
                'total_actions': total_actions,
                'error_rate_percent': round(error_rate, 2),
                'time_window': '1 hour'
            }
            
            if error_rate > 10:
                return 'CRITICAL', f'High error rate: {error_rate:.1f}%', details
            elif error_rate > 5:
                return 'WARNING', f'Elevated error rate: {error_rate:.1f}%', details
            else:
                return 'HEALTHY', f'Error rate normal: {error_rate:.1f}%', details
                
        except Exception as e:
            return 'WARNING', f'Error rate check failed: {str(e)}', {}
    
    def check_background_jobs(self) -> Tuple[str, str, Dict]:
        """Check background job queue status"""
        # This would integrate with your job queue system (RQ, Celery, etc.)
        
        details = {
            'note': 'Background job monitoring requires queue system integration'
        }
        
        return 'HEALTHY', 'Background job monitoring not implemented', details
    
    def send_alerts(self, results: Dict):
        """Send alerts for unhealthy conditions"""
        if not self.alerts:
            return
        
        alert_config = self.config.get('alerts', {})
        
        # Send Slack notification
        slack_webhook = alert_config.get('slack_webhook')
        if slack_webhook:
            self.send_slack_alert(slack_webhook, results)
        
        # Send email notification
        email_config = alert_config.get('email')
        if email_config:
            self.send_email_alert(email_config, results)
    
    def send_slack_alert(self, webhook_url: str, results: Dict):
        """Send Slack notification"""
        try:
            color = 'danger' if results['overall_status'] == 'UNHEALTHY' else 'warning'
            
            message = {
                'text': f"🚨 Health Check Alert - {results['overall_status']}",
                'attachments': [{
                    'color': color,
                    'fields': [
                        {
                            'title': alert['check'],
                            'value': f"{alert['status']}: {alert['message']}",
                            'short': False
                        }
                        for alert in self.alerts[:5]  # Limit to first 5 alerts
                    ],
                    'footer': 'Fraction Ball LMS Health Monitor',
                    'ts': int(time.time())
                }]
            }
            
            response = requests.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            
            self.logger.info("Slack alert sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
    
    def send_email_alert(self, email_config: Dict, results: Dict):
        """Send email notification"""
        try:
            subject = f"Health Check Alert - {results['overall_status']}"
            
            body = f"""
Health Check Results - {results['timestamp']}
Overall Status: {results['overall_status']}

Alerts:
"""
            
            for alert in self.alerts:
                body += f"- {alert['check']}: {alert['status']} - {alert['message']}\n"
            
            body += f"\nFull results available in monitoring dashboard."
            
            msg = MimeText(body)
            msg['Subject'] = subject
            msg['From'] = email_config['from']
            msg['To'] = ', '.join(email_config['to'])
            
            # Send email
            with smtplib.SMTP(email_config['smtp_host'], email_config.get('smtp_port', 587)) as server:
                if email_config.get('use_tls', True):
                    server.starttls()
                
                if email_config.get('username'):
                    server.login(email_config['username'], email_config['password'])
                
                server.send_message(msg)
            
            self.logger.info("Email alert sent successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")


def load_config(config_path: Optional[str]) -> Dict:
    """Load configuration from file or use defaults"""
    default_config = {
        'base_url': os.environ.get('HEALTH_CHECK_URL', 'http://localhost:8000'),
        'timeout': 30,
        'verbose': False,
        'alerts': {
            'slack_webhook': os.environ.get('SLACK_WEBHOOK_URL'),
            'email': {
                'from': os.environ.get('ALERT_EMAIL_FROM'),
                'to': os.environ.get('ALERT_EMAIL_TO', '').split(','),
                'smtp_host': os.environ.get('SMTP_HOST'),
                'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
                'username': os.environ.get('SMTP_USERNAME'),
                'password': os.environ.get('SMTP_PASSWORD'),
                'use_tls': os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
            }
        }
    }
    
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
                default_config.update(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}")
    
    return default_config


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Health monitoring for Fraction Ball LMS')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--output', help='Output file for results (JSON)')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    if args.verbose:
        config['verbose'] = True
    
    # Run health checks
    monitor = HealthMonitor(config)
    results = monitor.run_all_checks()
    
    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results written to {args.output}")
    else:
        print(json.dumps(results, indent=2))
    
    # Send alerts if needed
    if results['overall_status'] != 'HEALTHY':
        monitor.send_alerts(results)
    
    # Exit with appropriate code
    sys.exit(0 if results['overall_status'] == 'HEALTHY' else 1)


if __name__ == '__main__':
    main()
