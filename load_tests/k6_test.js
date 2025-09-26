/**
 * K6 Load Testing Script for Fraction Ball LMS
 * 
 * Test scenarios:
 * 1. Library browsing under load
 * 2. Dashboard loading performance
 * 3. API endpoint stress testing
 * 
 * Usage: k6 run --vus 100 --duration 5m load_tests/k6_test.js
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const libraryLoadTime = new Trend('library_load_time');
const dashboardLoadTime = new Trend('dashboard_load_time');
const apiResponseTime = new Trend('api_response_time');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 20 },   // Ramp up to 20 users
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '3m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<3000'], // 95% of requests must complete below 3s
    http_req_failed: ['rate<0.05'],    // Error rate must be below 5%
    errors: ['rate<0.1'],              // Custom error rate below 10%
    library_load_time: ['p(95)<2000'], // Library loads in under 2s
    dashboard_load_time: ['p(95)<3000'], // Dashboard loads in under 3s
  },
};

// Base configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_TOKEN = __ENV.API_TOKEN || 'test-token'; // Firebase JWT token

// Test data
const testUsers = [
  { email: 'teacher1@school1.edu', role: 'TEACHER' },
  { email: 'teacher2@school1.edu', role: 'TEACHER' },
  { email: 'admin@school1.edu', role: 'SCHOOL_ADMIN' },
];

const searchQueries = [
  'fractions',
  'basic math',
  'grade 3',
  'addition',
  'subtraction',
  'multiplication',
  'division',
  'geometry'
];

const filterCombinations = [
  { grade: 'K' },
  { grade: '1', topic: 'fractions_basics' },
  { grade: '2', topic: 'equivalent_fractions' },
  { topic: 'number_line' },
  { status: 'PUBLISHED' }
];

export function setup() {
  console.log('🚀 Starting load test setup...');
  
  // Health check
  const healthCheck = http.get(`${BASE_URL}/api/healthz/`);
  check(healthCheck, {
    'Health check passes': (r) => r.status === 200,
  });
  
  console.log('✅ Load test setup complete');
  return { baseUrl: BASE_URL, token: API_TOKEN };
}

export default function(data) {
  const headers = {
    'Authorization': `Bearer ${data.token}`,
    'Content-Type': 'application/json',
  };
  
  // Simulate different user behaviors
  const userBehavior = Math.random();
  
  if (userBehavior < 0.4) {
    // 40% - Library browsing scenario
    libraryBrowsingScenario(data, headers);
  } else if (userBehavior < 0.7) {
    // 30% - Dashboard usage scenario
    dashboardScenario(data, headers);
  } else if (userBehavior < 0.9) {
    // 20% - Search and filter scenario
    searchScenario(data, headers);
  } else {
    // 10% - Admin operations scenario
    adminScenario(data, headers);
  }
  
  // Random sleep between 1-3 seconds
  sleep(Math.random() * 2 + 1);
}

function libraryBrowsingScenario(data, headers) {
  const group = 'Library Browsing';
  
  // 1. Load library main page
  const libraryStart = Date.now();
  let response = http.get(`${data.baseUrl}/api/library/videos/`, { headers });
  const libraryTime = Date.now() - libraryStart;
  
  libraryLoadTime.add(libraryTime);
  
  const success = check(response, {
    [`${group}: Library loads successfully`]: (r) => r.status === 200,
    [`${group}: Library response time < 2s`]: (r) => r.timings.duration < 2000,
    [`${group}: Library has content`]: (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.results && data.results.length > 0;
      } catch (e) {
        return false;
      }
    },
  });
  
  if (!success) {
    errorRate.add(1);
    return;
  }
  
  // 2. Load video details
  try {
    const libraryData = JSON.parse(response.body);
    if (libraryData.results && libraryData.results.length > 0) {
      const randomVideo = libraryData.results[Math.floor(Math.random() * libraryData.results.length)];
      
      response = http.get(`${data.baseUrl}/api/library/videos/${randomVideo.id}/`, { headers });
      check(response, {
        [`${group}: Video detail loads`]: (r) => r.status === 200,
        [`${group}: Video detail response time < 1s`]: (r) => r.timings.duration < 1000,
      });
    }
  } catch (e) {
    errorRate.add(1);
  }
  
  // 3. Load resources
  response = http.get(`${data.baseUrl}/api/library/resources/`, { headers });
  check(response, {
    [`${group}: Resources load successfully`]: (r) => r.status === 200,
  });
  
  // 4. Load playlists
  response = http.get(`${data.baseUrl}/api/library/playlists/`, { headers });
  check(response, {
    [`${group}: Playlists load successfully`]: (r) => r.status === 200,
  });
}

function dashboardScenario(data, headers) {
  const group = 'Dashboard';
  
  // 1. Load teacher dashboard
  const dashboardStart = Date.now();
  let response = http.get(`${data.baseUrl}/api/dashboard/`, { headers });
  const dashboardTime = Date.now() - dashboardStart;
  
  dashboardLoadTime.add(dashboardTime);
  
  const success = check(response, {
    [`${group}: Dashboard loads successfully`]: (r) => r.status === 200,
    [`${group}: Dashboard response time < 3s`]: (r) => r.timings.duration < 3000,
    [`${group}: Dashboard has data`]: (r) => {
      try {
        const data = JSON.parse(r.body);
        return data.user_info && data.user_stats;
      } catch (e) {
        return false;
      }
    },
  });
  
  if (!success) {
    errorRate.add(1);
    return;
  }
  
  // 2. Load library stats
  response = http.get(`${data.baseUrl}/api/library/stats/`, { headers });
  check(response, {
    [`${group}: Library stats load`]: (r) => r.status === 200,
  });
  
  // 3. Load user's content status
  response = http.get(`${data.baseUrl}/api/approval/my-content-status/`, { headers });
  check(response, {
    [`${group}: Content status loads`]: (r) => r.status === 200,
  });
}

function searchScenario(data, headers) {
  const group = 'Search & Filter';
  
  // 1. Perform search
  const searchQuery = searchQueries[Math.floor(Math.random() * searchQueries.length)];
  let response = http.get(`${data.baseUrl}/api/library/videos/?search=${encodeURIComponent(searchQuery)}`, { headers });
  
  const success = check(response, {
    [`${group}: Search works`]: (r) => r.status === 200,
    [`${group}: Search response time < 2s`]: (r) => r.timings.duration < 2000,
  });
  
  if (!success) {
    errorRate.add(1);
    return;
  }
  
  // 2. Apply filters
  const filters = filterCombinations[Math.floor(Math.random() * filterCombinations.length)];
  const filterParams = new URLSearchParams(filters).toString();
  
  response = http.get(`${data.baseUrl}/api/library/videos/?${filterParams}`, { headers });
  check(response, {
    [`${group}: Filtering works`]: (r) => r.status === 200,
    [`${group}: Filter response time < 1.5s`]: (r) => r.timings.duration < 1500,
  });
  
  // 3. Combined search and filter
  response = http.get(
    `${data.baseUrl}/api/library/videos/?search=${encodeURIComponent(searchQuery)}&${filterParams}`, 
    { headers }
  );
  check(response, {
    [`${group}: Combined search+filter works`]: (r) => r.status === 200,
  });
}

function adminScenario(data, headers) {
  const group = 'Admin Operations';
  
  // 1. Load admin dashboard (may fail for non-admin users)
  let response = http.get(`${data.baseUrl}/api/admin/dashboard/`, { headers });
  check(response, {
    [`${group}: Admin dashboard accessible`]: (r) => r.status === 200 || r.status === 403,
  });
  
  // 2. Load approval queue
  response = http.get(`${data.baseUrl}/api/approval/videos/pending/`, { headers });
  check(response, {
    [`${group}: Approval queue loads`]: (r) => r.status === 200 || r.status === 403,
  });
  
  // 3. Load reports dashboard
  response = http.get(`${data.baseUrl}/api/reports/dashboard/`, { headers });
  check(response, {
    [`${group}: Reports dashboard loads`]: (r) => r.status === 200 || r.status === 403,
  });
}

export function teardown(data) {
  console.log('🏁 Load test completed');
  
  // Final health check
  const healthCheck = http.get(`${data.baseUrl}/api/healthz/`);
  check(healthCheck, {
    'System still healthy after load test': (r) => r.status === 200,
  });
}
