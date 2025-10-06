"""
Locust Load Testing Script for Fraction Ball LMS

Alternative to K6 for Python-based load testing

Usage:
    locust -f load_tests/locust_test.py --host=http://localhost:8000 --users=100 --spawn-rate=10
"""

import random
import json
from locust import HttpUser, task, between, events
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FractionBallUser(HttpUser):
    """Simulated user for load testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        self.token = "test-token"  # Firebase JWT token
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Test data
        self.search_queries = [
            "fractions", "basic math", "grade 3", "addition", 
            "subtraction", "multiplication", "division", "geometry"
        ]
        
        self.filter_combinations = [
            {"grade": "K"},
            {"grade": "1", "topic": "fractions_basics"},
            {"grade": "2", "topic": "equivalent_fractions"},
            {"topic": "number_line"},
            {"status": "PUBLISHED"}
        ]
        
        logger.info(f"User {self.user_id} started")
    
    def on_stop(self):
        """Called when a user stops"""
        logger.info(f"User {self.user_id} stopped")
    
    @task(4)
    def browse_library(self):
        """Library browsing - most common user activity (40% weight)"""
        with self.client.get("/api/library/videos/", 
                           headers=self.headers, 
                           name="library_videos",
                           catch_response=True) as response:
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("results"):
                        # Load a random video detail
                        video = random.choice(data["results"])
                        self.client.get(f"/api/library/videos/{video['id']}/",
                                      headers=self.headers,
                                      name="video_detail")
                    response.success()
                except (json.JSONDecodeError, KeyError):
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
        
        # Also load resources and playlists occasionally
        if random.random() < 0.3:
            self.client.get("/api/library/resources/", 
                          headers=self.headers,
                          name="library_resources")
        
        if random.random() < 0.2:
            self.client.get("/api/library/playlists/", 
                          headers=self.headers,
                          name="library_playlists")
    
    @task(3)
    def view_dashboard(self):
        """Dashboard viewing (30% weight)"""
        with self.client.get("/api/dashboard/", 
                           headers=self.headers,
                           name="dashboard",
                           catch_response=True) as response:
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "user_info" in data and "user_stats" in data:
                        response.success()
                    else:
                        response.failure("Missing dashboard data")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")
        
        # Load additional dashboard components
        if random.random() < 0.4:
            self.client.get("/api/library/stats/", 
                          headers=self.headers,
                          name="library_stats")
        
        if random.random() < 0.3:
            self.client.get("/api/approval/my-content-status/", 
                          headers=self.headers,
                          name="content_status")
    
    @task(2)
    def search_and_filter(self):
        """Search and filtering (20% weight)"""
        # Perform search
        query = random.choice(self.search_queries)
        self.client.get(f"/api/library/videos/?search={query}", 
                       headers=self.headers,
                       name="search_videos")
        
        # Apply filters
        filters = random.choice(self.filter_combinations)
        filter_params = "&".join([f"{k}={v}" for k, v in filters.items()])
        self.client.get(f"/api/library/videos/?{filter_params}", 
                       headers=self.headers,
                       name="filter_videos")
        
        # Combined search and filter
        if random.random() < 0.5:
            self.client.get(f"/api/library/videos/?search={query}&{filter_params}", 
                           headers=self.headers,
                           name="search_filter_combined")
    
    @task(1)
    def admin_operations(self):
        """Admin operations (10% weight)"""
        # These may fail for non-admin users, which is expected
        
        # Admin dashboard
        self.client.get("/api/admin/dashboard/", 
                       headers=self.headers,
                       name="admin_dashboard")
        
        # Approval queue
        self.client.get("/api/approval/videos/pending/", 
                       headers=self.headers,
                       name="approval_queue")
        
        # Reports dashboard
        self.client.get("/api/reports/dashboard/", 
                       headers=self.headers,
                       name="reports_dashboard")
        
        # User search
        if random.random() < 0.3:
            self.client.get("/api/admin/users/search/?q=teacher", 
                           headers=self.headers,
                           name="user_search")
    
    @task(1)
    def api_health_checks(self):
        """Health checks and system status (10% weight)"""
        self.client.get("/api/healthz/", name="health_check")
        
        # Public config (no auth required)
        self.client.get("/api/public-config/", name="public_config")
        
        # API documentation
        if random.random() < 0.1:
            self.client.get("/api/docs/", name="api_docs")


class TeacherUser(FractionBallUser):
    """Teacher-specific user behavior"""
    weight = 7  # 70% of users are teachers
    
    @task(1)
    def teacher_specific_actions(self):
        """Actions specific to teachers"""
        # Check content status more frequently
        self.client.get("/api/approval/my-content-status/", 
                       headers=self.headers,
                       name="teacher_content_status")
        
        # Browse own content
        self.client.get("/api/videos/?owner=me", 
                       headers=self.headers,
                       name="my_videos")
        
        # View playlists more often
        self.client.get("/api/playlists/", 
                       headers=self.headers,
                       name="my_playlists")


class AdminUser(FractionBallUser):
    """Admin-specific user behavior"""
    weight = 2  # 20% of users are admins
    
    @task(3)
    def admin_specific_actions(self):
        """Actions specific to admins"""
        # Admin dashboard more frequently
        self.client.get("/api/admin/dashboard/", 
                       headers=self.headers,
                       name="admin_dashboard_frequent")
        
        # User management
        self.client.get("/api/admin/users/search/", 
                       headers=self.headers,
                       name="admin_user_search")
        
        # Approval workflow
        self.client.get("/api/approval/videos/pending/", 
                       headers=self.headers,
                       name="admin_approval_queue")
        
        # System configuration
        if random.random() < 0.3:
            self.client.get("/api/config/system/", 
                           headers=self.headers,
                           name="system_config")


class AnonymousUser(FractionBallUser):
    """Anonymous user behavior (limited access)"""
    weight = 1  # 10% of users are anonymous
    
    def on_start(self):
        """Anonymous users don't have tokens"""
        self.headers = {"Content-Type": "application/json"}
        logger.info(f"Anonymous user {self.user_id} started")
    
    @task(5)
    def anonymous_actions(self):
        """Actions available to anonymous users"""
        # Public config only
        self.client.get("/api/public-config/", name="anon_public_config")
        
        # Health check
        self.client.get("/api/healthz/", name="anon_health_check")
        
        # Try to access protected resources (should fail)
        with self.client.get("/api/library/videos/", 
                           headers=self.headers,
                           name="anon_library_attempt",
                           catch_response=True) as response:
            if response.status_code in [401, 403]:
                response.success()  # Expected behavior
            else:
                response.failure(f"Expected 401/403, got {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts"""
    logger.info("🚀 Load test starting...")
    logger.info(f"Target host: {environment.host}")
    logger.info(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops"""
    logger.info("🏁 Load test completed")
    
    # Print summary statistics
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Failed requests: {stats.total.num_failures}")
    logger.info(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"95th percentile: {stats.total.get_response_time_percentile(0.95):.2f}ms")


@events.request_failure.add_listener
def on_request_failure(request_type, name, response_time, response_length, exception, **kwargs):
    """Called when a request fails"""
    logger.warning(f"Request failed: {request_type} {name} - {exception}")


# Custom event handlers for specific performance monitoring
@events.request_success.add_listener
def on_request_success(request_type, name, response_time, response_length, **kwargs):
    """Monitor successful requests for performance issues"""
    # Log slow requests
    if response_time > 3000:  # 3 seconds
        logger.warning(f"Slow request detected: {request_type} {name} - {response_time}ms")
    
    # Monitor specific endpoints
    if name in ["dashboard", "library_videos"] and response_time > 2000:
        logger.warning(f"Critical endpoint slow: {name} - {response_time}ms")


if __name__ == "__main__":
    # This allows running the script directly for testing
    import subprocess
    import sys
    
    print("Starting Locust load test...")
    print("Usage: locust -f load_tests/locust_test.py --host=http://localhost:8000")
    
    # You can add command line argument parsing here if needed










