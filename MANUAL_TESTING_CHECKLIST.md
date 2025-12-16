# Manual Testing Checklist

**Project:** Fraction Ball LMS  
**Date:** December 1, 2025  
**Version:** V4  

---

## 🔐 Security Testing

### Authentication
- [ ] Login with valid credentials succeeds
- [ ] Login with invalid credentials fails
- [ ] Logout works correctly
- [ ] Session expires after timeout
- [ ] Password reset flow works
- [ ] Can't access protected pages when logged out
- [ ] Firebase token validation works

### Authorization (RBAC)
- [ ] Teachers can upload content
- [ ] Teachers can view own uploads
- [ ] Teachers cannot access admin panel
- [ ] Admins can access admin panel
- [ ] School admins have appropriate permissions
- [ ] Users can only delete own content
- [ ] Users can only edit own content

### Data Isolation
- [ ] Users only see content from their school
- [ ] Public playlists visible within school only
- [ ] Private playlists only visible to owner
- [ ] Analytics filtered by school
- [ ] Cannot access other school's data via URL manipulation

### CSRF Protection
- [ ] All POST requests have CSRF token
- [ ] Forms submit successfully with token
- [ ] Requests fail without CSRF token
- [ ] Delete operations protected

---

## 📤 Functional Testing

### File Upload
- [ ] Can upload videos (.mp4, .mov, .avi)
- [ ] Can upload resources (PDF, DOCX, PPTX)
- [ ] File size validation works (reject too large)
- [ ] File type validation works (reject invalid types)
- [ ] Upload progress shows correctly
- [ ] Metadata saved correctly (title, description, grade, topic)
- [ ] Files stored in Firebase correctly
- [ ] Thumbnail generated (if applicable)

### Content Management
- [ ] View uploaded videos in "My Uploads"
- [ ] View uploaded resources in "My Uploads"
- [ ] Delete videos works
- [ ] Delete resources works
- [ ] Delete confirmation modal appears
- [ ] Edit content metadata works
- [ ] Content status changes (Draft → Pending → Published)

### Search & Filters
- [ ] Search by keyword works
- [ ] Filter by grade level works
- [ ] Filter by topic works
- [ ] Filter by location (classroom/court) works
- [ ] Multiple filters work together
- [ ] Search results are accurate
- [ ] "No results" message displays correctly
- [ ] Clear filters button works

### Playlists
- [ ] Can create new playlist
- [ ] Can add activities to playlist
- [ ] Can remove items from playlist
- [ ] Can reorder playlist items (if implemented)
- [ ] Can delete playlist
- [ ] Can duplicate playlist
- [ ] Can share playlist (generate link)
- [ ] Shared playlist accessible via link
- [ ] Share link expiration works
- [ ] Public playlists visible to school
- [ ] Private playlists only visible to owner

### Activities
- [ ] Browse all activities on home page
- [ ] Click activity to view details
- [ ] Video plays on activity detail page
- [ ] Download resources from activity page
- [ ] Prerequisites displayed correctly
- [ ] Learning objectives displayed
- [ ] Materials list displayed
- [ ] Game rules displayed
- [ ] Key terms displayed
- [ ] Related activities shown

### Community Forum
- [ ] View forum categories
- [ ] View recent posts
- [ ] Create new post
- [ ] Add comments to post
- [ ] Edit own posts
- [ ] Delete own posts
- [ ] Search forum posts
- [ ] Filter by category
- [ ] Pinned posts show at top
- [ ] Locked posts prevent new comments

### Analytics
- [ ] View analytics dashboard
- [ ] See total views and downloads
- [ ] See popular videos
- [ ] See popular resources
- [ ] Date range filter works
- [ ] Export to CSV works
- [ ] View trends chart displays
- [ ] Recent activity shows correctly

---

## 🎨 User Interface Testing

### Desktop Browsers
#### Chrome/Edge
- [ ] All pages load correctly
- [ ] No console errors
- [ ] Forms submit correctly
- [ ] Modals open and close
- [ ] Buttons respond to clicks
- [ ] Hover states work
- [ ] Animations smooth

#### Firefox
- [ ] All pages load correctly
- [ ] No console errors
- [ ] Forms submit correctly
- [ ] Video playback works
- [ ] Downloads work

#### Safari
- [ ] All pages load correctly
- [ ] No console errors
- [ ] Forms submit correctly
- [ ] Video playback works
- [ ] iOS-specific features work

### Mobile Devices
#### Mobile Safari (iOS)
- [ ] Home page responsive
- [ ] Navigation menu works
- [ ] Forms usable on mobile
- [ ] Touch gestures work
- [ ] Video playback works
- [ ] Downloads work
- [ ] Modals fit screen

#### Chrome Mobile (Android)
- [ ] Home page responsive
- [ ] Navigation menu works
- [ ] Forms usable on mobile
- [ ] Touch gestures work
- [ ] Video playback works
- [ ] File upload works

### Responsive Design
- [ ] Desktop (1920x1080) looks good
- [ ] Laptop (1366x768) looks good
- [ ] Tablet portrait (768x1024) looks good
- [ ] Tablet landscape (1024x768) looks good
- [ ] Mobile (375x667) looks good
- [ ] No horizontal scrolling
- [ ] Text readable at all sizes
- [ ] Images scale correctly
- [ ] Navigation accessible

### UI Elements
- [ ] All buttons clickable
- [ ] All links work correctly
- [ ] Forms validate input
- [ ] Error messages display clearly
- [ ] Success messages display
- [ ] Loading states show
- [ ] Empty states look good
- [ ] Icons display correctly
- [ ] Colors consistent
- [ ] Typography consistent

---

## ⚡ Performance Testing

### Page Load Times
- [ ] Home page loads < 2 seconds
- [ ] Activity detail < 1.5 seconds
- [ ] Playlists page < 1 second
- [ ] Analytics dashboard < 2 seconds
- [ ] Search results < 1 second

### Large Datasets
- [ ] Library with 100+ videos loads quickly
- [ ] Search with 100+ results performs well
- [ ] Analytics with months of data loads
- [ ] Pagination works smoothly
- [ ] Infinite scroll (if implemented) works

### Concurrent Users
- [ ] 10 users can access simultaneously
- [ ] Video streaming doesn't lag
- [ ] Database queries optimized
- [ ] No N+1 query problems
- [ ] Cache working correctly

### Network Conditions
- [ ] Works on fast connection (WiFi)
- [ ] Works on slow 3G
- [ ] Graceful degradation on poor connection
- [ ] Retry logic for failed requests
- [ ] Error messages for connection issues

---

## 📱 Accessibility Testing

### Screen Reader
- [ ] Can navigate with screen reader
- [ ] Alt text on images
- [ ] Form labels readable
- [ ] Buttons have descriptive text
- [ ] Error messages announced

### Keyboard Navigation
- [ ] Can tab through all elements
- [ ] Focus visible on all elements
- [ ] Enter key submits forms
- [ ] Escape closes modals
- [ ] Skip navigation link present

### Color Contrast
- [ ] Text readable against background
- [ ] Links distinguishable
- [ ] Buttons have good contrast
- [ ] No color-only information

---

## 🔧 Error Handling

### User Errors
- [ ] Invalid form submission shows errors
- [ ] Empty required fields highlighted
- [ ] Invalid file type rejected gracefully
- [ ] File too large shows clear message
- [ ] Network errors handled
- [ ] 404 page displays correctly
- [ ] 500 error page displays correctly

### Edge Cases
- [ ] Expired session handled
- [ ] Deleted content shows appropriate message
- [ ] Invalid URL parameters handled
- [ ] Missing data handled gracefully
- [ ] Special characters in input handled

---

## 📊 Data Integrity

### Database
- [ ] No orphaned records
- [ ] Foreign key relationships intact
- [ ] Cascade deletes work correctly
- [ ] Data validation at model level
- [ ] Constraints enforced

### File Storage
- [ ] Files uploaded successfully
- [ ] File paths correct
- [ ] No duplicate file names
- [ ] Deleted files removed
- [ ] Firebase storage organized

---

## 🚀 Workflow Testing

### Teacher Workflow
1. [ ] Login as teacher
2. [ ] Upload a video
3. [ ] Add metadata
4. [ ] Submit for approval
5. [ ] View in "My Uploads"
6. [ ] Create a playlist
7. [ ] Add video to playlist
8. [ ] Share playlist with colleague
9. [ ] View analytics
10. [ ] Export analytics

### Student/Viewer Workflow
1. [ ] Browse activities
2. [ ] Filter by grade level
3. [ ] Click activity to view
4. [ ] Watch instructional video
5. [ ] Download resources
6. [ ] View related activities
7. [ ] Access shared playlist

### Admin Workflow
1. [ ] Login as admin
2. [ ] View pending content
3. [ ] Approve/reject content
4. [ ] View school analytics
5. [ ] Manage users
6. [ ] View system logs

---

## ✅ Test Results

| Category | Tests Passed | Tests Failed | Pass Rate |
|----------|--------------|--------------|-----------|
| Security | / | / | % |
| Functional | / | / | % |
| UI | / | / | % |
| Performance | / | / | % |
| Accessibility | / | / | % |
| **TOTAL** | **/ ** | **/ ** | **%** |

---

## 📝 Notes & Issues

### Critical Issues
- [ ] None found

### Minor Issues
- [ ] None found

### Improvements Needed
- [ ] TBD

---

## 👤 Testers

| Name | Role | Date | Signature |
|------|------|------|-----------|
| | | | |
| | | | |

---

## 📋 Test Environment

- **OS:** macOS / Windows / Linux
- **Browser:** Chrome ___ / Firefox ___ / Safari ___
- **Screen Size:** ___x___
- **Network:** WiFi / 4G / 3G
- **Device:** Desktop / Laptop / Tablet / Mobile

---

## ✅ Sign-Off

I certify that all tests have been completed and the results documented above.

**Tester Name:** ___________________  
**Date:** ___________________  
**Signature:** ___________________

---

**End of Manual Testing Checklist**

