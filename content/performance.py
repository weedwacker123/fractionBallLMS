"""
Performance optimization utilities and query optimization
"""
from django.core.cache import cache
from django.db import models
from django.db.models import Prefetch, Count, Q
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Utility class for optimizing database queries"""
    
    @staticmethod
    def optimize_video_queryset(queryset):
        """Optimize VideoAsset queryset with proper select_related and prefetch_related"""
        return queryset.select_related(
            'owner',
            'school', 
            'reviewed_by'
        ).prefetch_related(
            Prefetch(
                'views',
                queryset=models.Q(viewed_at__gte=timezone.now() - timedelta(days=30))
            ),
            'playlistitem_set__playlist'
        )
    
    @staticmethod
    def optimize_playlist_queryset(queryset):
        """Optimize Playlist queryset"""
        return queryset.select_related(
            'owner',
            'school'
        ).prefetch_related(
            Prefetch(
                'playlistitem_set',
                queryset=models.Q().select_related('video_asset').order_by('order')
            )
        ).annotate(
            video_count=Count('playlistitem_set'),
            total_duration=models.Sum('playlistitem_set__video_asset__duration')
        )
    
    @staticmethod
    def optimize_user_queryset(queryset):
        """Optimize User queryset"""
        return queryset.select_related('school').annotate(
            video_count=Count('videoasset', filter=Q(videoasset__status='PUBLISHED')),
            resource_count=Count('resource', filter=Q(resource__status='PUBLISHED'))
        )


class CacheManager:
    """Centralized cache management"""
    
    # Cache timeouts
    SHORT_CACHE = 300  # 5 minutes
    MEDIUM_CACHE = 1800  # 30 minutes
    LONG_CACHE = 3600  # 1 hour
    DAY_CACHE = 86400  # 24 hours
    
    @staticmethod
    def generate_cache_key(prefix, *args, **kwargs):
        """Generate consistent cache keys"""
        key_parts = [str(prefix)]
        key_parts.extend([str(arg) for arg in args])
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        
        key_string = ":".join(key_parts)
        # Use hash if key is too long
        if len(key_string) > 200:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        return key_string
    
    @classmethod
    def get_or_set_library_cache(cls, cache_key, queryset_func, timeout=MEDIUM_CACHE):
        """Cache library query results"""
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            data = queryset_func()
            cache.set(cache_key, data, timeout)
            return data
        except Exception as e:
            logger.error(f"Cache set failed for {cache_key}: {e}")
            return queryset_func()  # Return uncached data
    
    @classmethod
    def invalidate_user_cache(cls, user_id):
        """Invalidate all cache entries for a specific user"""
        patterns = [
            f"dashboard:user:{user_id}",
            f"library:user:{user_id}:*",
            f"playlists:user:{user_id}:*",
            f"analytics:user:{user_id}:*"
        ]
        
        for pattern in patterns:
            try:
                cache.delete_pattern(pattern)
            except AttributeError:
                # Redis cache backend supports delete_pattern, others may not
                pass
    
    @classmethod
    def invalidate_school_cache(cls, school_id):
        """Invalidate all cache entries for a specific school"""
        patterns = [
            f"library:school:{school_id}:*",
            f"analytics:school:{school_id}:*",
            f"dashboard:school:{school_id}:*"
        ]
        
        for pattern in patterns:
            try:
                cache.delete_pattern(pattern)
            except AttributeError:
                pass


class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    @staticmethod
    def log_slow_query(query_name, execution_time, threshold=1.0):
        """Log queries that exceed performance threshold"""
        if execution_time > threshold:
            logger.warning(
                f"Slow query detected: {query_name} took {execution_time:.2f}s "
                f"(threshold: {threshold}s)"
            )
    
    @staticmethod
    def measure_query_performance(func):
        """Decorator to measure query performance"""
        def wrapper(*args, **kwargs):
            start_time = timezone.now()
            result = func(*args, **kwargs)
            end_time = timezone.now()
            
            execution_time = (end_time - start_time).total_seconds()
            PerformanceMonitor.log_slow_query(
                func.__name__, 
                execution_time
            )
            
            return result
        return wrapper


def optimize_library_queries():
    """Apply optimizations to library queries"""
    from .models import VideoAsset, Resource, Playlist
    
    # Pre-warm cache for popular content
    try:
        # Cache popular videos
        popular_videos = VideoAsset.objects.filter(
            status='PUBLISHED'
        ).annotate(
            view_count=Count('views')
        ).order_by('-view_count')[:20]
        
        cache_key = CacheManager.generate_cache_key('popular_videos')
        cache.set(cache_key, list(popular_videos.values()), CacheManager.LONG_CACHE)
        
        # Cache recent content
        recent_videos = VideoAsset.objects.filter(
            status='PUBLISHED',
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:50]
        
        cache_key = CacheManager.generate_cache_key('recent_videos')
        cache.set(cache_key, list(recent_videos.values()), CacheManager.MEDIUM_CACHE)
        
        logger.info("Library cache pre-warmed successfully")
        
    except Exception as e:
        logger.error(f"Failed to pre-warm library cache: {e}")


def clear_expired_cache():
    """Clear expired cache entries (run periodically)"""
    try:
        # Clear old analytics cache
        patterns_to_clear = [
            'analytics:*:old',
            'dashboard:*:expired',
            'library:*:stale'
        ]
        
        for pattern in patterns_to_clear:
            try:
                cache.delete_pattern(pattern)
            except AttributeError:
                pass
        
        logger.info("Expired cache cleared successfully")
        
    except Exception as e:
        logger.error(f"Failed to clear expired cache: {e}")


class DatabaseOptimizer:
    """Database-level optimizations"""
    
    @staticmethod
    def analyze_query_performance():
        """Analyze and report on query performance"""
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                # Get slow query log (PostgreSQL specific)
                cursor.execute("""
                    SELECT query, total_time, calls, mean_time
                    FROM pg_stat_statements 
                    WHERE mean_time > 100 
                    ORDER BY mean_time DESC 
                    LIMIT 10
                """)
                
                slow_queries = cursor.fetchall()
                
                if slow_queries:
                    logger.warning(f"Found {len(slow_queries)} slow queries")
                    for query_data in slow_queries:
                        logger.warning(
                            f"Slow query: {query_data[3]:.2f}ms avg, "
                            f"{query_data[2]} calls - {query_data[0][:100]}..."
                        )
                else:
                    logger.info("No slow queries detected")
                    
        except Exception as e:
            logger.info(f"Query analysis not available: {e}")
    
    @staticmethod
    def update_table_statistics():
        """Update database table statistics for better query planning"""
        from django.db import connection
        
        try:
            with connection.cursor() as cursor:
                # Update statistics for main tables (PostgreSQL)
                tables = [
                    'content_videoasset',
                    'content_resource', 
                    'content_playlist',
                    'content_assetview',
                    'accounts_user'
                ]
                
                for table in tables:
                    cursor.execute(f"ANALYZE {table}")
                
                logger.info("Database statistics updated")
                
        except Exception as e:
            logger.error(f"Failed to update database statistics: {e}")


# Performance monitoring decorators
def cache_result(timeout=CacheManager.MEDIUM_CACHE, key_prefix="cached"):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = CacheManager.generate_cache_key(
                key_prefix,
                func.__name__,
                *args,
                **kwargs
            )
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        
        return wrapper
    return decorator


def invalidate_cache_on_change(cache_patterns):
    """Decorator to invalidate cache when data changes"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate specified cache patterns
            for pattern in cache_patterns:
                try:
                    cache.delete_pattern(pattern)
                except AttributeError:
                    # Fallback for cache backends without pattern deletion
                    cache.clear()
                    break
            
            return result
        return wrapper
    return decorator
