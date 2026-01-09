"""
Taxonomy Service for fetching dynamic taxonomies from Firestore CMS

This service provides cached access to taxonomies (grades, topics, court types)
from the CMS Firestore collection, replacing hardcoded choices in models.py
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Cache TTL in seconds (30 seconds for quick CMS updates)
TAXONOMY_CACHE_TTL = getattr(settings, 'TAXONOMY_CACHE_TTL', 30)

# Fallback values if Firestore is unavailable and cache is empty
FALLBACK_GRADES = [
    {'key': 'K', 'label': 'Kindergarten'},
    {'key': '1', 'label': 'Grade 1'},
    {'key': '2', 'label': 'Grade 2'},
    {'key': '3', 'label': 'Grade 3'},
    {'key': '4', 'label': 'Grade 4'},
    {'key': '5', 'label': 'Grade 5'},
    {'key': '6', 'label': 'Grade 6'},
    {'key': '7', 'label': 'Grade 7'},
    {'key': '8', 'label': 'Grade 8'},
]

FALLBACK_TOPICS = [
    {'key': 'fractions_basics', 'label': 'Fractions Basics'},
    {'key': 'equivalent_fractions', 'label': 'Equivalent Fractions'},
    {'key': 'comparing_ordering', 'label': 'Comparing/Ordering'},
    {'key': 'number_line', 'label': 'Number Line'},
    {'key': 'mixed_improper', 'label': 'Mixed ↔ Improper'},
    {'key': 'add_subtract_fractions', 'label': 'Add/Subtract Fractions'},
    {'key': 'multiply_divide_fractions', 'label': 'Multiply/Divide Fractions (6+)'},
    {'key': 'decimals_percents', 'label': 'Decimals & Percents'},
    {'key': 'ratio_proportion', 'label': 'Ratio/Proportion (6+)'},
    {'key': 'word_problems', 'label': 'Word Problems'},
]

FALLBACK_COURT_TYPES = [
    {'key': 'classroom', 'label': 'Classroom'},
    {'key': 'court', 'label': 'Court'},
    {'key': 'both', 'label': 'Both'},
]


def _get_firestore_client():
    """Get Firestore client - reuse from firestore_service"""
    from content.firestore_service import get_firestore_client
    return get_firestore_client()


def _fetch_taxonomy_from_firestore(taxonomy_type: str) -> List[Dict[str, Any]]:
    """
    Fetch taxonomy values from Firestore by type

    Args:
        taxonomy_type: 'topic', 'court', 'grade', or 'standard'

    Returns:
        List of taxonomy values with key, label, description, color
    """
    try:
        db = _get_firestore_client()
        docs = db.collection('taxonomies').where('type', '==', taxonomy_type).where('active', '==', True).order_by('displayOrder').stream()

        all_values = []
        for doc in docs:
            data = doc.to_dict()
            values = data.get('values', [])
            all_values.extend(values)

        logger.info(f"Fetched {len(all_values)} values for taxonomy type '{taxonomy_type}'")
        return all_values

    except Exception as e:
        logger.error(f"Error fetching taxonomy '{taxonomy_type}' from Firestore: {e}")
        return []


def get_grade_levels() -> List[Dict[str, Any]]:
    """
    Get grade levels from cache or Firestore

    Returns:
        List of dicts with 'key' and 'label' (e.g., [{'key': 'K', 'label': 'Kindergarten'}, ...])
    """
    cache_key = 'taxonomy:grades'

    # Try cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch from Firestore
    grades = _fetch_taxonomy_from_firestore('grade')

    # Use fallback if empty
    if not grades:
        logger.warning("Using fallback grade levels - Firestore unavailable or empty")
        grades = FALLBACK_GRADES

    # Cache and return
    cache.set(cache_key, grades, TAXONOMY_CACHE_TTL)
    return grades


def get_topics() -> List[Dict[str, Any]]:
    """
    Get topic taxonomies from cache or Firestore

    Returns:
        List of dicts with 'key', 'label', and optionally 'description', 'color'
    """
    cache_key = 'taxonomy:topics'

    # Try cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch from Firestore
    topics = _fetch_taxonomy_from_firestore('topic')

    # Use fallback if empty
    if not topics:
        logger.warning("Using fallback topics - Firestore unavailable or empty")
        topics = FALLBACK_TOPICS

    # Cache and return
    cache.set(cache_key, topics, TAXONOMY_CACHE_TTL)
    return topics


def get_court_types() -> List[Dict[str, Any]]:
    """
    Get court/location types from cache or Firestore

    Returns:
        List of dicts with 'key' and 'label'
    """
    cache_key = 'taxonomy:courtTypes'

    # Try cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch from Firestore
    court_types = _fetch_taxonomy_from_firestore('court')

    # Use fallback if empty
    if not court_types:
        logger.warning("Using fallback court types - Firestore unavailable or empty")
        court_types = FALLBACK_COURT_TYPES

    # Cache and return
    cache.set(cache_key, court_types, TAXONOMY_CACHE_TTL)
    return court_types


def get_grade_choices() -> List[Tuple[str, str]]:
    """
    Get grade levels formatted for Django model choices

    Returns:
        List of tuples: [('K', 'Kindergarten'), ('1', 'Grade 1'), ...]
    """
    grades = get_grade_levels()
    return [(g['key'], g['label']) for g in grades]


def get_topic_choices() -> List[Tuple[str, str]]:
    """
    Get topics formatted for Django model choices

    Returns:
        List of tuples: [('fractions_basics', 'Fractions Basics'), ...]
    """
    topics = get_topics()
    return [(t['key'], t['label']) for t in topics]


def get_court_type_choices() -> List[Tuple[str, str]]:
    """
    Get court types formatted for Django model choices

    Returns:
        List of tuples: [('classroom', 'Classroom'), ...]
    """
    court_types = get_court_types()
    return [(c['key'], c['label']) for c in court_types]


def get_grade_keys() -> List[str]:
    """
    Get just the grade keys for use in templates

    Returns:
        List of grade keys: ['K', '1', '2', ...]
    """
    grades = get_grade_levels()
    return [g['key'] for g in grades]


def get_topic_keys() -> List[str]:
    """
    Get just the topic keys for use in templates

    Returns:
        List of topic keys: ['fractions_basics', ...]
    """
    topics = get_topics()
    return [t['key'] for t in topics]


def is_valid_grade(grade: str) -> bool:
    """
    Check if a grade value is valid

    Args:
        grade: Grade key to validate

    Returns:
        True if valid, False otherwise
    """
    valid_grades = get_grade_keys()
    return grade in valid_grades


def is_valid_topic(topic: str) -> bool:
    """
    Check if a topic value is valid

    Args:
        topic: Topic key to validate

    Returns:
        True if valid, False otherwise
    """
    valid_topics = get_topic_keys()
    return topic in valid_topics


def is_valid_court_type(court_type: str) -> bool:
    """
    Check if a court type value is valid

    Args:
        court_type: Court type key to validate

    Returns:
        True if valid, False otherwise
    """
    court_types = get_court_types()
    valid_keys = [c['key'] for c in court_types]
    return court_type in valid_keys


def refresh_cache():
    """
    Force refresh all taxonomy caches
    Call this when you know taxonomies have changed in CMS
    """
    cache.delete('taxonomy:grades')
    cache.delete('taxonomy:topics')
    cache.delete('taxonomy:courtTypes')

    # Pre-populate caches
    get_grade_levels()
    get_topics()
    get_court_types()

    logger.info("Taxonomy caches refreshed")


def get_all_taxonomies() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all taxonomies at once (efficient for initial page load)

    Returns:
        Dict with 'grades', 'topics', 'courtTypes' keys
    """
    return {
        'grades': get_grade_levels(),
        'topics': get_topics(),
        'courtTypes': get_court_types(),
    }
