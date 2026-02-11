"""
Community forum views for discussion, collaboration, and sharing
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse, Http404
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Q, Count
from django.conf import settings
from .models import ForumPost, ForumComment, ForumCategory, Activity
from . import firestore_service
from .firestore_adapters import FirestoreCommunityPost, FirestoreComment, FirestoreCategoryProxy
import logging

logger = logging.getLogger(__name__)


def community_home(request):
    """
    Main community page with forum posts
    """
    # Get filter parameters
    category_slug = request.GET.get('category', '')
    search_query = request.GET.get('q', '')

    if getattr(settings, 'USE_FIRESTORE', False):
        # Firestore path
        posts_data = firestore_service.get_community_posts(
            limit=20,
            category=category_slug if category_slug else None,
            search=search_query if search_query else None,
        )
        posts = [FirestoreCommunityPost.from_dict(p) for p in posts_data]

        # Build categories with post counts from unfiltered data
        if category_slug or search_query:
            all_posts_data = firestore_service.get_community_posts(limit=200)
        else:
            all_posts_data = posts_data
        categories = FirestoreCategoryProxy.get_all_categories(all_posts_data)
    else:
        # Django ORM path (fallback)
        categories = ForumCategory.objects.filter(is_active=True).annotate(
            post_count=Count('forumpost')
        )

        posts = ForumPost.objects.select_related('author', 'category').annotate(
            comment_count=Count('comments')
        )

        if category_slug:
            posts = posts.filter(category__slug=category_slug)

        if search_query:
            posts = posts.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query)
            )

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
    use_firestore = getattr(settings, 'USE_FIRESTORE', False)
    used_firestore = False

    if use_firestore:
        # Firestore path
        post_data = firestore_service.get_community_post_by_slug(slug)
        if post_data:
            used_firestore = True
            post = FirestoreCommunityPost.from_dict(post_data)

            # Increment view count (fire-and-forget)
            try:
                firestore_service.increment_post_view_count(post.id)
                post.view_count += 1
            except Exception:
                pass

            # Build threaded comments
            all_comments = post.comments
            top_level = []
            replies_map = {}

            for comment in all_comments:
                if comment.is_deleted:
                    continue
                if comment.parent_comment_id:
                    replies_map.setdefault(comment.parent_comment_id, []).append(comment)
                else:
                    top_level.append(comment)

            for comment in top_level:
                comment._replies_list = replies_map.get(comment.id, [])

            comments = top_level
            can_comment = not post.is_locked

    if not used_firestore:
        # Django ORM path (also used as fallback when Firestore post not found)
        post = get_object_or_404(
            ForumPost.objects.select_related('author', 'category'),
            slug=slug
        )

        post.view_count += 1
        post.save(update_fields=['view_count'])

        comments = post.comments.filter(
            is_deleted=False,
            parent_comment=None
        ).select_related('author').prefetch_related('replies__author')

        can_comment = not post.is_locked

    context = {
        'post': post,
        'comments': comments,
        'can_comment': can_comment,
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

            # Sync to Firestore (non-blocking)
            try:
                from content.firestore_service import create_community_post
                create_community_post(str(post.id), {
                    'title': post.title,
                    'content': post.content,
                    'slug': post.slug,
                    'authorId': request.user.firebase_uid,
                    'authorName': request.user.get_full_name(),
                    'category': post.category.name if post.category else None,
                    'status': 'active',
                    'viewCount': 0,
                    'createdAt': post.created_at.isoformat(),
                    'lastActivityAt': post.last_activity_at.isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to sync post to Firestore: {e}")
            messages.success(request, f'Post "{title}" created successfully!')
            return redirect('v4:community-post-detail', slug=post.slug)
            
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

        # Sync to Firestore (non-blocking)
        try:
            from content.firestore_service import add_comment_to_post
            add_comment_to_post(str(post.id), str(comment.id), {
                'content': comment.content,
                'authorId': request.user.firebase_uid,
                'authorName': request.user.get_full_name(),
                'parentCommentId': str(parent_comment.id) if parent_comment else None,
                'createdAt': comment.created_at.isoformat(),
                'isDeleted': False
            })
        except Exception as e:
            logger.warning(f"Failed to sync comment to Firestore: {e}")
        
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

        # Sync to Firestore (non-blocking)
        try:
            from content.firestore_service import delete_community_post
            delete_community_post(str(post_id))
        except Exception as e:
            logger.warning(f"Failed to delete post from Firestore: {e}")

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

        # Sync to Firestore (non-blocking)
        try:
            from content.firestore_service import delete_comment as firestore_delete_comment
            firestore_delete_comment(str(comment.post.id), str(comment_id))
        except Exception as e:
            logger.warning(f"Failed to sync comment deletion to Firestore: {e}")

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
@require_POST
def flag_post(request, post_id):
    """
    Flag a post as inappropriate for moderator review
    Teachers can flag posts, admins will see them in CMS
    """
    try:
        post = get_object_or_404(ForumPost, id=post_id)

        # Don't allow flagging own posts
        if post.author == request.user:
            return JsonResponse({
                'success': False,
                'message': 'You cannot flag your own post'
            }, status=400)

        reason = request.POST.get('reason', '').strip()
        if not reason:
            return JsonResponse({
                'success': False,
                'message': 'Please provide a reason for flagging'
            }, status=400)

        logger.info(f"Post {post_id} flagged by {request.user.username}: {reason}")

        # Sync flag to Firestore for CMS moderation
        try:
            from content.firestore_service import update_community_post
            update_community_post(str(post_id), {
                'isFlagged': True,
                'flagReason': reason,
                'flaggedAt': timezone.now().isoformat(),
                'flaggedBy': request.user.firebase_uid,
                'status': 'flagged'
            })
        except Exception as e:
            logger.error(f"Failed to sync flag to Firestore: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Failed to submit flag. Please try again.'
            }, status=500)

        return JsonResponse({
            'success': True,
            'message': 'Thank you for reporting. Our moderators will review this post.'
        })

    except Exception as e:
        logger.error(f"Failed to flag post: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to flag post: {str(e)}'
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
        return redirect('v4:community-post-detail', slug=post.slug)
    
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

            # Sync to Firestore (non-blocking)
            try:
                from content.firestore_service import update_community_post
                update_community_post(str(post.id), {
                    'title': post.title,
                    'content': post.content,
                    'category': post.category.name if post.category else None,
                    'updatedAt': timezone.now().isoformat()
                })
            except Exception as e:
                logger.warning(f"Failed to sync post update to Firestore: {e}")

            messages.success(request, 'Post updated successfully!')
            return redirect('v4:community-post-detail', slug=post.slug)
            
        except Exception as e:
            logger.error(f"Failed to update post: {e}")
            messages.error(request, f'Failed to update post: {str(e)}')
    
    # GET - show form
    context = {
        'post': post,
        'categories': ForumCategory.objects.filter(is_active=True)
    }
    return render(request, 'community_edit_post.html', context)

