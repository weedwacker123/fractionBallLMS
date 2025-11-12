"""
Views for Fraction Ball V4 interface
Educational activity-focused UI
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .models import VideoAsset, Resource


def home(request):
    """
    Main home page with activity cards
    """
    context = {
        'selected_grade': request.GET.get('grade', '5'),
        'selected_topics': request.GET.getlist('topic', ['fractions']),
    }
    return render(request, 'home.html', context)


def activity_detail(request, slug):
    """
    Activity detail page with prerequisites, objectives, materials, etc.
    """
    # For now, return a static page
    # In production, this would fetch from database
    context = {
        'activity': {
            'title': 'Field Cone Frenzy',
            'slug': slug,
            'grade': '5',
            'activity_number': '1',
        }
    }
    return render(request, 'activity_detail.html', context)


def community(request):
    """
    Community page for teacher collaboration
    """
    return render(request, 'community.html')


def faq(request):
    """
    FAQ page
    """
    return render(request, 'faq.html')


@login_required
def my_notes(request):
    """
    User's notes on activities
    """
    # Future implementation
    return render(request, 'notes.html')


def search_activities(request):
    """
    Search/filter activities
    """
    query = request.GET.get('q', '')
    grade = request.GET.get('grade', '')
    topics = request.GET.getlist('topic', [])
    
    # Future: Implement actual search
    # For now, redirect to home with filters
    context = {
        'query': query,
        'grade': grade,
        'topics': topics,
    }
    return render(request, 'home.html', context)









