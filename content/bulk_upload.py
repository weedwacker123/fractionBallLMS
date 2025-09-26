"""
Bulk upload system for CSV content ingestion with background job processing
"""
import csv
import io
import uuid
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, EmailValidator
from .models import VideoAsset, Resource, GRADE_CHOICES, TOPIC_CHOICES
from accounts.models import School
from content.models import AuditLog
import logging
import json

logger = logging.getLogger(__name__)
User = get_user_model()


class BulkUploadJob:
    """
    Background job for processing bulk uploads
    """
    
    def __init__(self, job_id, user_id, school_id, file_content, file_type='video'):
        self.job_id = job_id
        self.user_id = user_id
        self.school_id = school_id
        self.file_content = file_content
        self.file_type = file_type
        self.results = {
            'status': 'RUNNING',
            'total_rows': 0,
            'processed_rows': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'errors': [],
            'warnings': [],
            'created_items': [],
            'started_at': timezone.now().isoformat(),
            'completed_at': None,
            'processing_time': None
        }
    
    def process(self):
        """Main processing method"""
        try:
            logger.info(f"Starting bulk upload job {self.job_id}")
            
            # Get user and school
            user = User.objects.get(id=self.user_id)
            school = School.objects.get(id=self.school_id)
            
            # Parse CSV content
            csv_data = self.parse_csv(self.file_content)
            self.results['total_rows'] = len(csv_data)
            
            if self.file_type == 'video':
                self.process_video_uploads(csv_data, user, school)
            elif self.file_type == 'resource':
                self.process_resource_uploads(csv_data, user, school)
            else:
                raise ValueError(f"Unsupported file type: {self.file_type}")
            
            # Mark as completed
            self.results['status'] = 'COMPLETED'
            self.results['completed_at'] = timezone.now().isoformat()
            
            # Calculate processing time
            started = datetime.fromisoformat(self.results['started_at'].replace('Z', '+00:00'))
            completed = datetime.fromisoformat(self.results['completed_at'].replace('Z', '+00:00'))
            self.results['processing_time'] = (completed - started).total_seconds()
            
            logger.info(f"Bulk upload job {self.job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Bulk upload job {self.job_id} failed: {e}")
            self.results['status'] = 'FAILED'
            self.results['completed_at'] = timezone.now().isoformat()
            self.results['errors'].append({
                'type': 'SYSTEM_ERROR',
                'message': str(e),
                'row': None
            })
        
        return self.results
    
    def parse_csv(self, file_content):
        """Parse CSV content and return list of dictionaries"""
        csv_data = []
        
        try:
            # Handle both string and bytes
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            for row_num, row in enumerate(csv_reader, start=1):
                # Clean up the row data
                cleaned_row = {}
                for key, value in row.items():
                    if key:  # Skip empty column names
                        cleaned_row[key.strip()] = value.strip() if value else ''
                
                cleaned_row['_row_number'] = row_num
                csv_data.append(cleaned_row)
            
            return csv_data
            
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}")
    
    def process_video_uploads(self, csv_data, user, school):
        """Process video asset uploads"""
        required_fields = ['title', 'storage_uri']
        optional_fields = ['description', 'grade', 'topic', 'tags', 'duration', 'owner_email']
        
        for row in csv_data:
            row_num = row.get('_row_number', 0)
            self.results['processed_rows'] += 1
            
            try:
                # Validate required fields
                missing_fields = []
                for field in required_fields:
                    if not row.get(field):
                        missing_fields.append(field)
                
                if missing_fields:
                    self.add_error(row_num, 'VALIDATION_ERROR', 
                                 f"Missing required fields: {', '.join(missing_fields)}")
                    continue
                
                # Determine owner
                owner = user  # Default to the user who initiated the upload
                owner_email = row.get('owner_email', '').strip()
                if owner_email:
                    try:
                        owner = User.objects.get(email=owner_email, school=school)
                    except User.DoesNotExist:
                        self.add_warning(row_num, 'OWNER_NOT_FOUND', 
                                       f"Owner email {owner_email} not found, using uploader as owner")
                
                # Validate and convert fields
                video_data = self.validate_video_data(row, row_num)
                if not video_data:
                    continue  # Validation errors already recorded
                
                # Create video asset
                with transaction.atomic():
                    video = VideoAsset.objects.create(
                        title=video_data['title'],
                        description=video_data.get('description', ''),
                        grade=video_data.get('grade'),
                        topic=video_data.get('topic'),
                        tags=video_data.get('tags', []),
                        duration=video_data.get('duration'),
                        storage_uri=video_data['storage_uri'],
                        owner=owner,
                        school=school,
                        status='DRAFT'  # All bulk uploads start as drafts
                    )
                    
                    self.results['successful_imports'] += 1
                    self.results['created_items'].append({
                        'type': 'video',
                        'id': str(video.id),
                        'title': video.title,
                        'row': row_num
                    })
                    
                    # Log creation
                    AuditLog.objects.create(
                        action='CONTENT_BULK_IMPORTED',
                        user=user,
                        metadata={
                            'job_id': self.job_id,
                            'content_type': 'video',
                            'content_id': str(video.id),
                            'content_title': video.title,
                            'row_number': row_num,
                            'actual_owner': owner.email
                        }
                    )
                
            except Exception as e:
                logger.error(f"Failed to process video row {row_num}: {e}")
                self.add_error(row_num, 'PROCESSING_ERROR', str(e))
    
    def process_resource_uploads(self, csv_data, user, school):
        """Process resource uploads"""
        required_fields = ['title', 'file_uri', 'file_type']
        optional_fields = ['description', 'grade', 'topic', 'tags', 'owner_email']
        
        for row in csv_data:
            row_num = row.get('_row_number', 0)
            self.results['processed_rows'] += 1
            
            try:
                # Validate required fields
                missing_fields = []
                for field in required_fields:
                    if not row.get(field):
                        missing_fields.append(field)
                
                if missing_fields:
                    self.add_error(row_num, 'VALIDATION_ERROR', 
                                 f"Missing required fields: {', '.join(missing_fields)}")
                    continue
                
                # Determine owner
                owner = user
                owner_email = row.get('owner_email', '').strip()
                if owner_email:
                    try:
                        owner = User.objects.get(email=owner_email, school=school)
                    except User.DoesNotExist:
                        self.add_warning(row_num, 'OWNER_NOT_FOUND', 
                                       f"Owner email {owner_email} not found, using uploader as owner")
                
                # Validate and convert fields
                resource_data = self.validate_resource_data(row, row_num)
                if not resource_data:
                    continue
                
                # Create resource
                with transaction.atomic():
                    resource = Resource.objects.create(
                        title=resource_data['title'],
                        description=resource_data.get('description', ''),
                        file_uri=resource_data['file_uri'],
                        file_type=resource_data['file_type'],
                        grade=resource_data.get('grade'),
                        topic=resource_data.get('topic'),
                        tags=resource_data.get('tags', []),
                        owner=owner,
                        school=school,
                        status='DRAFT'
                    )
                    
                    self.results['successful_imports'] += 1
                    self.results['created_items'].append({
                        'type': 'resource',
                        'id': str(resource.id),
                        'title': resource.title,
                        'row': row_num
                    })
                    
                    # Log creation
                    AuditLog.objects.create(
                        action='CONTENT_BULK_IMPORTED',
                        user=user,
                        metadata={
                            'job_id': self.job_id,
                            'content_type': 'resource',
                            'content_id': str(resource.id),
                            'content_title': resource.title,
                            'row_number': row_num,
                            'actual_owner': owner.email
                        }
                    )
                
            except Exception as e:
                logger.error(f"Failed to process resource row {row_num}: {e}")
                self.add_error(row_num, 'PROCESSING_ERROR', str(e))
    
    def validate_video_data(self, row, row_num):
        """Validate video data from CSV row"""
        try:
            data = {}
            
            # Title
            data['title'] = row['title'].strip()
            if len(data['title']) < 3:
                self.add_error(row_num, 'VALIDATION_ERROR', "Title must be at least 3 characters")
                return None
            
            # Storage URI
            data['storage_uri'] = row['storage_uri'].strip()
            try:
                URLValidator()(data['storage_uri'])
            except ValidationError:
                self.add_error(row_num, 'VALIDATION_ERROR', "Invalid storage URI format")
                return None
            
            # Description (optional)
            if row.get('description'):
                data['description'] = row['description'].strip()
            
            # Grade (optional)
            grade = row.get('grade', '').strip()
            if grade:
                grade_choices = [choice[0] for choice in GRADE_CHOICES]
                if grade not in grade_choices:
                    self.add_error(row_num, 'VALIDATION_ERROR', 
                                 f"Invalid grade: {grade}. Valid choices: {', '.join(grade_choices)}")
                    return None
                data['grade'] = grade
            
            # Topic (optional)
            topic = row.get('topic', '').strip()
            if topic:
                topic_choices = [choice[0] for choice in TOPIC_CHOICES]
                if topic not in topic_choices:
                    self.add_error(row_num, 'VALIDATION_ERROR', 
                                 f"Invalid topic: {topic}. Valid choices: {', '.join(topic_choices)}")
                    return None
                data['topic'] = topic
            
            # Tags (optional, comma-separated)
            tags_str = row.get('tags', '').strip()
            if tags_str:
                data['tags'] = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            
            # Duration (optional, in seconds)
            duration_str = row.get('duration', '').strip()
            if duration_str:
                try:
                    data['duration'] = int(duration_str)
                    if data['duration'] < 0:
                        self.add_error(row_num, 'VALIDATION_ERROR', "Duration must be positive")
                        return None
                except ValueError:
                    self.add_error(row_num, 'VALIDATION_ERROR', "Duration must be a number (seconds)")
                    return None
            
            return data
            
        except Exception as e:
            self.add_error(row_num, 'VALIDATION_ERROR', f"Data validation failed: {e}")
            return None
    
    def validate_resource_data(self, row, row_num):
        """Validate resource data from CSV row"""
        try:
            data = {}
            
            # Title
            data['title'] = row['title'].strip()
            if len(data['title']) < 3:
                self.add_error(row_num, 'VALIDATION_ERROR', "Title must be at least 3 characters")
                return None
            
            # File URI
            data['file_uri'] = row['file_uri'].strip()
            try:
                URLValidator()(data['file_uri'])
            except ValidationError:
                self.add_error(row_num, 'VALIDATION_ERROR', "Invalid file URI format")
                return None
            
            # File type
            data['file_type'] = row['file_type'].strip().lower()
            valid_types = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'image', 'other']
            if data['file_type'] not in valid_types:
                self.add_warning(row_num, 'FILE_TYPE_WARNING', 
                               f"Unknown file type: {data['file_type']}, setting to 'other'")
                data['file_type'] = 'other'
            
            # Description (optional)
            if row.get('description'):
                data['description'] = row['description'].strip()
            
            # Grade and topic validation (same as video)
            grade = row.get('grade', '').strip()
            if grade:
                grade_choices = [choice[0] for choice in GRADE_CHOICES]
                if grade not in grade_choices:
                    self.add_error(row_num, 'VALIDATION_ERROR', 
                                 f"Invalid grade: {grade}. Valid choices: {', '.join(grade_choices)}")
                    return None
                data['grade'] = grade
            
            topic = row.get('topic', '').strip()
            if topic:
                topic_choices = [choice[0] for choice in TOPIC_CHOICES]
                if topic not in topic_choices:
                    self.add_error(row_num, 'VALIDATION_ERROR', 
                                 f"Invalid topic: {topic}. Valid choices: {', '.join(topic_choices)}")
                    return None
                data['topic'] = topic
            
            # Tags
            tags_str = row.get('tags', '').strip()
            if tags_str:
                data['tags'] = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
            
            return data
            
        except Exception as e:
            self.add_error(row_num, 'VALIDATION_ERROR', f"Data validation failed: {e}")
            return None
    
    def add_error(self, row_num, error_type, message):
        """Add an error to the results"""
        self.results['failed_imports'] += 1
        self.results['errors'].append({
            'row': row_num,
            'type': error_type,
            'message': message
        })
    
    def add_warning(self, row_num, warning_type, message):
        """Add a warning to the results"""
        self.results['warnings'].append({
            'row': row_num,
            'type': warning_type,
            'message': message
        })


def create_bulk_upload_job(user, file_content, file_type='video'):
    """
    Create and queue a bulk upload job
    """
    job_id = str(uuid.uuid4())
    
    # Create job instance
    job = BulkUploadJob(
        job_id=job_id,
        user_id=user.id,
        school_id=user.school.id,
        file_content=file_content,
        file_type=file_type
    )
    
    # Store job in cache for status tracking
    from django.core.cache import cache
    cache.set(f'bulk_upload_job:{job_id}', {
        'status': 'QUEUED',
        'created_at': timezone.now().isoformat(),
        'user_id': str(user.id),
        'file_type': file_type
    }, timeout=3600 * 24)  # 24 hours
    
    # Queue the job (in a real implementation, this would use RQ)
    # For now, we'll process synchronously for simplicity
    try:
        results = job.process()
        cache.set(f'bulk_upload_job:{job_id}', results, timeout=3600 * 24)
        return job_id, results
    except Exception as e:
        error_results = {
            'status': 'FAILED',
            'error': str(e),
            'created_at': timezone.now().isoformat()
        }
        cache.set(f'bulk_upload_job:{job_id}', error_results, timeout=3600 * 24)
        return job_id, error_results


def get_job_status(job_id):
    """
    Get the status of a bulk upload job
    """
    from django.core.cache import cache
    return cache.get(f'bulk_upload_job:{job_id}')


def cleanup_old_jobs():
    """
    Clean up old job records (should be run periodically)
    """
    from django.core.cache import cache
    # This is a simplified cleanup - in production you'd iterate through job keys
    # and remove old ones based on timestamps
    pass
