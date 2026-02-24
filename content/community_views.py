"""
Community forum views for discussion, collaboration, and sharing
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.utils.text import slugify
from django.utils import timezone
from django.db.models import Q, Count
from django.conf import settings
from .models import ForumPost, ForumComment, ForumCategory, Activity
from . import firestore_service
from .firestore_adapters import (
    FirestoreCommunityPost, FirestoreComment, FirestoreCategoryProxy,
    FirestoreActivity,
)
import logging
import uuid

logger = logging.getLogger(__name__)


def _use_firestore():
    return getattr(settings, 'USE_FIRESTORE', False)


def _get_form_context():
    """Get categories and activities for create/edit post forms."""
    if _use_firestore():
        categories = FirestoreCategoryProxy.get_all_categories()
        activities_data = firestore_service.get_published_activities()
        activities = [FirestoreActivity.from_dict(a) for a in activities_data]
    else:
        categories = ForumCategory.objects.filter(is_active=True)
        activities = Activity.objects.filter(is_published=True)[:50]
    return {'categories': categories, 'activities': activities}


def _can_community_access(user):
    return user.is_authenticated and user.can('community.create')


def _can_moderate_community(user):
    return user.is_authenticated and user.can('community.moderate')


def community_home(request):
    """
    Main community page with forum posts
    """
    if not _can_community_access(request.user):
        return HttpResponseForbidden("Missing required permission: community.create")

    # Get filter parameters
    category_slug = request.GET.get('category', '')
    search_query = request.GET.get('q', '')

    if _use_firestore():
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
    if not _can_community_access(request.user):
        return HttpResponseForbidden("Missing required permission: community.create")

    use_firestore = _use_firestore()
    used_firestore = False
    is_author = False

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

            # Check if current user is the author
            user_uid = getattr(request.user, 'firebase_uid', '') if request.user.is_authenticated else ''
            is_author = bool(user_uid and post.author_id == user_uid)

            # Build threaded comments
            all_comments = post.comments
            top_level = []
            replies_map = {}

            for comment in all_comments:
                if comment.is_deleted:
                    continue
                # Mark if current user owns this comment
                comment.is_own = bool(user_uid and comment.author_id == user_uid)
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
        is_author = request.user.is_authenticated and post.author == request.user

    context = {
        'post': post,
        'comments': comments,
        'can_comment': can_comment,
        'is_author': is_author,
    }
    return render(request, 'community_post_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_post(request):
    """
    Create a new forum post
    """
    if not _can_community_access(request.user):
        return HttpResponseForbidden("Missing required permission: community.create")

    if request.method == 'POST':
        try:
            title = request.POST.get('title', '').strip()
            content = request.POST.get('content', '').strip()
            category_key = request.POST.get('category', '')
            activity_id = request.POST.get('activity', '')

            # Validation
            if not title or not content:
                messages.error(request, 'Title and content are required')
                return render(request, 'community_create_post.html', _get_form_context())

            if _use_firestore():
                # Firestore path - create post directly in Firestore
                base_slug = slugify(title)
                slug = base_slug
                counter = 1
                while firestore_service.check_community_slug_exists(slug):
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                post_id = str(uuid.uuid4())
                now = timezone.now()

                post_data = {
                    'title': title,
                    'content': content,
                    'slug': slug,
                    'category': category_key if category_key else '',
                    'authorId': request.user.firebase_uid,
                    'authorName': request.user.get_full_name() or request.user.username,
                    'status': 'active',
                    'viewCount': 0,
                    'commentCount': 0,
                    'isPinned': False,
                    'isLocked': False,
                    'createdAt': now,
                    'lastActivityAt': now,
                }

                if activity_id:
                    post_data['relatedActivityId'] = activity_id

                firestore_service.create_community_post(post_id, post_data)
                logger.info(f"Community post created in Firestore: {post_id} by {request.user.username}")

                messages.success(request, f'Post "{title}" created successfully!')
                return redirect('v4:community-post-detail', slug=slug)
            else:
                # Django ORM path
                slug = slugify(title)
                original_slug = slug
                counter = 1
                while ForumPost.objects.filter(slug=slug).exists():
                    slug = f"{original_slug}-{counter}"
                    counter += 1

                # Get category if provided
                category = None
                if category_key:
                    try:
                        category = ForumCategory.objects.get(id=category_key)
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
                    firestore_service.create_community_post(str(post.id), {
                        'title': post.title,
                        'content': post.content,
                        'slug': post.slug,
                        'authorId': request.user.firebase_uid,
                        'authorName': request.user.get_full_name(),
                        'category': post.category.name if post.category else None,
                        'status': 'active',
                        'viewCount': 0,
                        'createdAt': post.created_at,
                        'lastActivityAt': post.last_activity_at
                    })
                except Exception as e:
                    logger.warning(f"Failed to sync post to Firestore: {e}")

                messages.success(request, f'Post "{title}" created successfully!')
                return redirect('v4:community-post-detail', slug=post.slug)

        except Exception as e:
            logger.error(f"Failed to create post: {e}")
            messages.error(request, f'Failed to create post: {str(e)}')

    # GET - show form
    return render(request, 'community_create_post.html', _get_form_context())


@login_required
@require_POST
def add_comment(request, post_slug):
    """
    Add a comment to a post
    """
    if not _can_community_access(request.user):
        return JsonResponse(
            {'success': False, 'message': 'Missing required permission: community.create'},
            status=403
        )

    try:
        if _use_firestore():
            # Firestore path
            post_data = firestore_service.get_community_post_by_slug(post_slug)
            if not post_data:
                return JsonResponse({
                    'success': False,
                    'message': 'Post not found'
                }, status=404)

            if post_data.get('isLocked', False):
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

            comment_id = str(uuid.uuid4())
            now = timezone.now()
            author_name = request.user.get_full_name() or request.user.username

            comment_data = {
                'content': content,
                'authorId': request.user.firebase_uid,
                'authorName': author_name,
                'parentCommentId': parent_id if parent_id else None,
                'createdAt': now,
                'isDeleted': False,
            }

            firestore_service.add_comment_to_post(post_data['id'], comment_id, comment_data)

            # Update post's last activity time and comment count
            from firebase_admin import firestore as fb_firestore
            firestore_service.update_community_post(post_data['id'], {
                'lastActivityAt': now,
                'commentCount': fb_firestore.Increment(1),
            })

            logger.info(f"Comment added to Firestore post {post_data['id']} by {request.user.username}")

            return JsonResponse({
                'success': True,
                'message': 'Comment added successfully',
                'comment': {
                    'id': comment_id,
                    'author': author_name,
                    'content': content,
                    'created_at': now.strftime('%B %d, %Y at %I:%M %p')
                }
            })
        else:
            # Django ORM path
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
                firestore_service.add_comment_to_post(str(post.id), str(comment.id), {
                    'content': comment.content,
                    'authorId': request.user.firebase_uid,
                    'authorName': request.user.get_full_name(),
                    'parentCommentId': str(parent_comment.id) if parent_comment else None,
                    'createdAt': comment.created_at,
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
        if _use_firestore():
            post_data = firestore_service.get_document('communityPosts', post_id)
            if not post_data:
                return JsonResponse({
                    'success': False,
                    'message': 'Post not found'
                }, status=404)

            user_uid = getattr(request.user, 'firebase_uid', '')
            is_author = post_data.get('authorId') == user_uid
            if not is_author and not _can_moderate_community(request.user):
                return JsonResponse({
                    'success': False,
                    'message': 'You do not have permission to delete this post'
                }, status=403)

            post_title = post_data.get('title', '')
            firestore_service.delete_community_post(post_id)
            logger.info(f"Forum post deleted from Firestore: {post_id} by {request.user.username}")

            return JsonResponse({
                'success': True,
                'message': f'Post "{post_title}" deleted successfully'
            })
        else:
            post = get_object_or_404(ForumPost, id=post_id)

            # Check permission (must be author or admin)
            if post.author != request.user and not _can_moderate_community(request.user):
                return JsonResponse({
                    'success': False,
                    'message': 'You do not have permission to delete this post'
                }, status=403)

            post_title = post.title
            post.delete()

            logger.info(f"Forum post deleted: {post_id} by {request.user.username}")

            # Sync to Firestore (non-blocking)
            try:
                firestore_service.delete_community_post(str(post_id))
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
def delete_comment(request, post_id, comment_id):
    """
    Delete a comment (author or admin only)
    """
    try:
        if _use_firestore():
            # Read the comment from Firestore subcollection
            db = firestore_service.get_firestore_client()
            comment_doc = db.collection('communityPosts').document(
                post_id
            ).collection('comments').document(comment_id).get()

            if not comment_doc.exists:
                return JsonResponse({
                    'success': False,
                    'message': 'Comment not found'
                }, status=404)

            comment_data = comment_doc.to_dict()
            user_uid = getattr(request.user, 'firebase_uid', '')
            is_own = comment_data.get('authorId') == user_uid

            if not is_own and not _can_moderate_community(request.user):
                return JsonResponse({
                    'success': False,
                    'message': 'You do not have permission to delete this comment'
                }, status=403)

            firestore_service.delete_comment(post_id, comment_id)
            logger.info(f"Comment soft-deleted in Firestore: {comment_id} by {request.user.username}")

            return JsonResponse({
                'success': True,
                'message': 'Comment deleted successfully'
            })
        else:
            comment = get_object_or_404(ForumComment, id=comment_id)

            # Check permission
            if comment.author != request.user and not _can_moderate_community(request.user):
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
                firestore_service.delete_comment(str(comment.post.id), str(comment_id))
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
    if not _can_community_access(request.user):
        return JsonResponse(
            {'success': False, 'message': 'Missing required permission: community.create'},
            status=403
        )

    try:
        if _use_firestore():
            post_data = firestore_service.get_document('communityPosts', post_id)
            if not post_data:
                return JsonResponse({
                    'success': False,
                    'message': 'Post not found'
                }, status=404)

            user_uid = getattr(request.user, 'firebase_uid', '')
            if post_data.get('authorId') == user_uid:
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

            firestore_service.update_community_post(post_id, {
                'isFlagged': True,
                'flagReason': reason,
                'flaggedAt': timezone.now(),
                'flaggedBy': user_uid,
                'status': 'flagged',
            })

            logger.info(f"Post {post_id} flagged by {request.user.username}: {reason}")

            return JsonResponse({
                'success': True,
                'message': 'Thank you for reporting. Our moderators will review this post.'
            })
        else:
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
                firestore_service.update_community_post(str(post_id), {
                    'isFlagged': True,
                    'flagReason': reason,
                    'flaggedAt': timezone.now(),
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
    if not _can_community_access(request.user):
        return HttpResponseForbidden("Missing required permission: community.create")

    if _use_firestore():
        post_data = firestore_service.get_document('communityPosts', post_id)
        if not post_data:
            raise Http404("Post not found")

        post = FirestoreCommunityPost.from_dict(post_data)

        # Check permission - must be author
        user_uid = getattr(request.user, 'firebase_uid', '')
        if post.author_id != user_uid:
            messages.error(request, 'You can only edit your own posts')
            return redirect('v4:community-post-detail', slug=post.slug)

        if request.method == 'POST':
            try:
                title = request.POST.get('title', '').strip()
                content = request.POST.get('content', '').strip()
                category_key = request.POST.get('category', '')

                if not title or not content:
                    messages.error(request, 'Title and content are required')
                    context = _get_form_context()
                    context['post'] = post
                    return render(request, 'community_edit_post.html', context)

                updates = {
                    'title': title,
                    'content': content,
                    'category': category_key if category_key else '',
                    'updatedAt': timezone.now(),
                }
                firestore_service.update_community_post(post_id, updates)

                logger.info(f"Post updated in Firestore: {post_id} by {request.user.username}")
                messages.success(request, 'Post updated successfully!')
                return redirect('v4:community-post-detail', slug=post.slug)

            except Exception as e:
                logger.error(f"Failed to update post: {e}")
                messages.error(request, f'Failed to update post: {str(e)}')

        # GET - show form
        context = _get_form_context()
        context['post'] = post
        return render(request, 'community_edit_post.html', context)
    else:
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
                    firestore_service.update_community_post(str(post.id), {
                        'title': post.title,
                        'content': post.content,
                        'category': post.category.name if post.category else None,
                        'updatedAt': timezone.now()
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
