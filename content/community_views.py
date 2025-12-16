"""
Community forum views for discussion, collaboration, and sharing
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Q, Count
from .models import ForumPost, ForumComment, ForumCategory, Activity
import logging

logger = logging.getLogger(__name__)


def community_home(request):
    """
    Main community page with forum posts
    """
    # Get filter parameters
    category_slug = request.GET.get('category', '')
    search_query = request.GET.get('q', '')
    
    # Get all categories with post counts
    categories = ForumCategory.objects.filter(is_active=True).annotate(
        post_count=Count('forumpost')
    )
    
    # Build query
    posts = ForumPost.objects.select_related('author', 'category').annotate(
        comment_count=Count('comments')
    )
    
    # Apply filters
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Order: pinned first, then by last activity
    posts = posts.order_by('-is_pinned', '-last_activity_at')[:20]
    
    context = {
        'posts': posts,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': search_query,
    }
    return render(request, 'community.html', context)


def post_detail(request, slug):
    """
    Individual post detail page with comments
    """
    post = get_object_or_404(
        ForumPost.objects.select_related('author', 'category'),
        slug=slug
    )
    
    # Increment view count
    post.view_count += 1
    post.save(update_fields=['view_count'])
    
    # Get comments with author info
    comments = post.comments.filter(
        is_deleted=False,
        parent_comment=None  # Top-level comments only
    ).select_related('author').prefetch_related('replies__author')
    
    context = {
        'post': post,
        'comments': comments,
        'can_comment': not post.is_locked,
    }
    return render(request, 'community_post_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_post(request):
    """
    Create a new forum post
    """
    if request.method == 'POST':
        try:
            title = request.POST.get('title', '').strip()
            content = request.POST.get('content', '').strip()
            category_id = request.POST.get('category', '')
            activity_id = request.POST.get('activity', '')
            
            # Validation
            if not title or not content:
                messages.error(request, 'Title and content are required')
                return render(request, 'community_create_post.html', {
                    'categories': ForumCategory.objects.filter(is_active=True),
                    'activities': Activity.objects.filter(is_published=True)[:50]
                })
            
            # Generate unique slug
            slug = slugify(title)
            original_slug = slug
            counter = 1
            while ForumPost.objects.filter(slug=slug).exists():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            # Get category if provided
            category = None
            if category_id:
                try:
                    category = ForumCategory.objects.get(id=category_id)
                except ForumCategory.DoesNotExist:
                    pass
            
            # Get activity if provided
            activity = None
            if activity_id:
                try:
                    activity = Activity.objects.get(id=activity_id)
                except Activity.DoesNotExist:
                    pass
            
            # Create post
            post = ForumPost.objects.create(
                title=title,
                slug=slug,
                content=content,
                author=request.user,
                category=category,
                related_activity=activity
            )
            
            logger.info(f"Forum post created: {post.id} by {request.user.username}")
            messages.success(request, f'Post "{title}" created successfully!')
            return redirect('community-post-detail', slug=post.slug)
            
        except Exception as e:
            logger.error(f"Failed to create post: {e}")
            messages.error(request, f'Failed to create post: {str(e)}')
    
    # GET - show form
    context = {
        'categories': ForumCategory.objects.filter(is_active=True),
        'activities': Activity.objects.filter(is_published=True)[:50]
    }
    return render(request, 'community_create_post.html', context)


@login_required
@require_POST
def add_comment(request, post_slug):
    """
    Add a comment to a post
    """
    try:
        post = get_object_or_404(ForumPost, slug=post_slug)
        
        # Check if post is locked
        if post.is_locked:
            return JsonResponse({
                'success': False,
                'message': 'This post is locked and no longer accepting comments'
            }, status=403)
        
        content = request.POST.get('content', '').strip()
        parent_id = request.POST.get('parent_id', '')
        
        if not content:
            return JsonResponse({
                'success': False,
                'message': 'Comment content is required'
            }, status=400)
        
        # Get parent comment if replying
        parent_comment = None
        if parent_id:
            try:
                parent_comment = ForumComment.objects.get(id=parent_id, post=post)
            except ForumComment.DoesNotExist:
                pass
        
        # Create comment
        comment = ForumComment.objects.create(
            post=post,
            author=request.user,
            content=content,
            parent_comment=parent_comment
        )
        
        # Update post's last activity
        post.last_activity_at = timezone.now()
        post.save(update_fields=['last_activity_at'])
        
        logger.info(f"Comment added to post {post.id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Comment added successfully',
            'comment': {
                'id': str(comment.id),
                'author': comment.author_name,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p')
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to add comment: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to add comment: {str(e)}'
        }, status=500)


@login_required
@require_POST
def delete_post(request, post_id):
    """
    Delete a post (author or admin only)
    """
    try:
        post = get_object_or_404(ForumPost, id=post_id)
        
        # Check permission (must be author or admin)
        if post.author != request.user and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to delete this post'
            }, status=403)
        
        post_title = post.title
        post.delete()
        
        logger.info(f"Forum post deleted: {post_id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f'Post "{post_title}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to delete post: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to delete post: {str(e)}'
        }, status=500)


@login_required
@require_POST
def delete_comment(request, comment_id):
    """
    Delete a comment (author or admin only)
    """
    try:
        comment = get_object_or_404(ForumComment, id=comment_id)
        
        # Check permission
        if comment.author != request.user and not request.user.is_staff:
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to delete this comment'
            }, status=403)
        
        # Soft delete (mark as deleted)
        comment.is_deleted = True
        comment.save(update_fields=['is_deleted'])
        
        logger.info(f"Comment deleted: {comment_id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': 'Comment deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to delete comment: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to delete comment: {str(e)}'
        }, status=500)


@login_required
@require_http_methods(["GET", "POST"])
def edit_post(request, post_id):
    """
    Edit an existing post (author only)
    """
    post = get_object_or_404(ForumPost, id=post_id)
    
    # Check permission
    if post.author != request.user:
        messages.error(request, 'You can only edit your own posts')
        return redirect('community-post-detail', slug=post.slug)
    
    if request.method == 'POST':
        try:
            title = request.POST.get('title', '').strip()
            content = request.POST.get('content', '').strip()
            category_id = request.POST.get('category', '')
            
            if not title or not content:
                messages.error(request, 'Title and content are required')
                return render(request, 'community_edit_post.html', {
                    'post': post,
                    'categories': ForumCategory.objects.filter(is_active=True)
                })
            
            post.title = title
            post.content = content
            
            # Update category if provided
            if category_id:
                try:
                    post.category = ForumCategory.objects.get(id=category_id)
                except ForumCategory.DoesNotExist:
                    pass
            
            post.save()
            
            messages.success(request, 'Post updated successfully!')
            return redirect('community-post-detail', slug=post.slug)
            
        except Exception as e:
            logger.error(f"Failed to update post: {e}")
            messages.error(request, f'Failed to update post: {str(e)}')
    
    # GET - show form
    context = {
        'post': post,
        'categories': ForumCategory.objects.filter(is_active=True)
    }
    return render(request, 'community_edit_post.html', context)

