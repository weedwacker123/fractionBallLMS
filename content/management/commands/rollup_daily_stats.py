from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from content.models import VideoAsset, AssetView, DailyAssetStats
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Rollup daily asset statistics for performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to process (YYYY-MM-DD). Defaults to yesterday.'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to process (default: 1)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recalculation of existing stats'
        )

    def handle(self, *args, **options):
        target_date = options.get('date')
        days_count = options['days']
        force_recalc = options['force']

        if target_date:
            try:
                start_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD.')
                )
                return
        else:
            # Default to yesterday
            start_date = (timezone.now() - timedelta(days=1)).date()

        self.stdout.write(f'📊 Rolling up daily statistics...')
        self.stdout.write(f'Start date: {start_date}')
        self.stdout.write(f'Processing {days_count} day(s)')

        total_processed = 0
        total_created = 0
        total_updated = 0

        for day_offset in range(days_count):
            current_date = start_date + timedelta(days=day_offset)
            
            self.stdout.write(f'\n📅 Processing {current_date}...')
            
            created, updated = self.process_date(current_date, force_recalc)
            total_created += created
            total_updated += updated
            total_processed += 1
            
            self.stdout.write(f'   ✅ Created: {created}, Updated: {updated}')

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 Daily stats rollup completed!\n'
                f'   • Processed {total_processed} days\n'
                f'   • Created {total_created} new records\n'
                f'   • Updated {total_updated} existing records'
            )
        )

    def process_date(self, date, force_recalc=False):
        """Process analytics for a specific date"""
        created_count = 0
        updated_count = 0
        
        # Get date range (start of day to end of day)
        start_datetime = datetime.combine(date, datetime.min.time())
        end_datetime = datetime.combine(date, datetime.max.time())
        
        # Make timezone aware
        start_datetime = timezone.make_aware(start_datetime)
        end_datetime = timezone.make_aware(end_datetime)
        
        # Get all videos that had views on this date
        videos_with_views = VideoAsset.objects.filter(
            views__viewed_at__range=(start_datetime, end_datetime)
        ).distinct()
        
        for video in videos_with_views:
            # Check if stats already exist
            daily_stats, created = DailyAssetStats.objects.get_or_create(
                asset=video,
                date=date,
                defaults={
                    'view_count': 0,
                    'unique_viewers': 0,
                    'total_watch_time': 0,
                    'avg_completion_rate': 0.0,
                    'playlist_adds': 0
                }
            )
            
            if created:
                created_count += 1
            elif not force_recalc:
                # Skip if already exists and not forcing recalculation
                continue
            else:
                updated_count += 1
            
            # Calculate statistics for this video on this date
            views_queryset = AssetView.objects.filter(
                asset=video,
                viewed_at__range=(start_datetime, end_datetime)
            )
            
            stats = views_queryset.aggregate(
                view_count=Count('id'),
                unique_viewers=Count('user', distinct=True),
                total_watch_time=Sum('duration_watched'),
                avg_completion_rate=Avg('completion_percentage')
            )
            
            # Count playlist additions (approximate - when playlist items were created)
            from .models import PlaylistItem
            playlist_adds = PlaylistItem.objects.filter(
                video_asset=video,
                created_at__range=(start_datetime, end_datetime)
            ).count()
            
            # Update the daily stats record
            daily_stats.view_count = stats['view_count'] or 0
            daily_stats.unique_viewers = stats['unique_viewers'] or 0
            daily_stats.total_watch_time = stats['total_watch_time'] or 0
            daily_stats.avg_completion_rate = stats['avg_completion_rate'] or 0.0
            daily_stats.playlist_adds = playlist_adds
            
            with transaction.atomic():
                daily_stats.save()
        
        return created_count, updated_count

    def cleanup_old_stats(self, days_to_keep=365):
        """Clean up old daily stats to save space"""
        cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)
        
        deleted_count = DailyAssetStats.objects.filter(
            date__lt=cutoff_date
        ).delete()[0]
        
        if deleted_count > 0:
            self.stdout.write(
                f'🗑️  Cleaned up {deleted_count} old daily stats records'
            )






