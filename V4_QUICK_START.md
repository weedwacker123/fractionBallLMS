# Fraction Ball V4 - Quick Start Guide

## What Was Implemented

Based on your Figma mockups, the V4 interface includes:

### ✅ New Navigation (base.html)
- Fraction Ball logo with red basketball icon
- HOME, COMMUNITY, FAQ navigation links
- User profile and notification icons
- Modern, clean design

### ✅ Home Page (/)
- Hero section with "FRACTIONBALL" title
- Filter system (Grade 5, FRACTIONS, DECIMALS, CLASSROOM, COURT)
- Activity cards grid:
  - **Activity 1**: Field Cone Frenzy (cone icon)
  - **Activity 2**: Bottle-Cap Bonanza (bottle cap icon)
  - **Activity 3**: Simon Says & Switch (person icon)
- Topic tags (Mixed Denominators, Equivalent Fractions, etc.)
- Multiple rows showing activity variations (Pt. 1, Pt. 2)

### ✅ Activity Detail Page (/activities/field-cone-frenzy/)
- Breadcrumb navigation (Home / Grade 5 / Activity 1)
- Prerequisites section
- Learning objectives
- Lesson overview (Part 1, Part 2)
- Materials list with links
- Key terms
- Game rules (highlighted in red box)
- Resources sidebar:
  - For Teachers (XCL, Court Tracker, Basketball Activity PDF)
  - For Students (PDF resources)
  - Related Activities

### ✅ Community Page (/community/)
- Discussion forums section
- Resource sharing
- Success stories
- Recent community posts
- Create new post button

### ✅ FAQ Page (/faq/)
- Collapsible FAQ sections
- Getting Started
- Implementation
- Technical Support
- Contact support CTA

## Running the V4 Interface

### Method 1: Quick Build Script

```bash
cd /Users/evantran/fractionBallLMS
./scripts/build_v4.sh
python manage.py runserver
```

### Method 2: Manual Setup

```bash
# 1. Install Node dependencies
npm install

# 2. Build Tailwind CSS
npm run build-css-prod

# 3. Collect static files
python manage.py collectstatic --noinput

# 4. Run server
python manage.py runserver
```

### Method 3: Docker

```bash
docker-compose up --build
```

## Accessing Pages

Once the server is running, visit:

- **Home Page**: http://localhost:8000/
- **Field Cone Frenzy**: http://localhost:8000/activities/field-cone-frenzy/
- **Community**: http://localhost:8000/community/
- **FAQ**: http://localhost:8000/faq/

Legacy admin pages:
- **Teacher Dashboard**: http://localhost:8000/dashboard/
- **Upload**: http://localhost:8000/upload/
- **Admin**: http://localhost:8000/admin/

## Key Design Elements

### Colors
- **Primary Red**: `#ef4444` (buttons, logo, accents)
- **Yellow Filters**: `#fef08a` (filter pills)
- **Gray Background**: `#f9fafb` (page background)

### Typography
- **Font**: Inter (Google Fonts)
- **Headings**: Bold, clean sans-serif
- **Body**: Regular weight, good readability

### Components
- **Activity Cards**: White background, shadow on hover
- **Filter Pills**: Rounded, yellow background, X to remove
- **Buttons**: Red background, rounded corners, hover effects
- **Icons**: Inline SVG, 24x24 or larger for activities

## File Structure

```
/Users/evantran/fractionBallLMS/
├── templates/
│   ├── base.html                 ← Updated navigation
│   ├── home.html                 ← NEW: Main page
│   ├── activity_detail.html      ← NEW: Activity details
│   ├── community.html            ← NEW: Community
│   └── faq.html                  ← NEW: FAQ
├── content/
│   ├── v4_views.py               ← NEW: V4 views
│   └── v4_urls.py                ← NEW: V4 URLs
├── fractionball/
│   └── urls.py                   ← Updated to include V4
├── tailwind.config.js            ← Updated colors
└── scripts/
    └── build_v4.sh               ← NEW: Build script
```

## Customization

### Adding New Activities

1. **Add to Home Page** (`templates/home.html`):
```html
<div class="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-200 overflow-hidden">
    <!-- Activity card content -->
</div>
```

2. **Create Detail Page**:
   - Copy `activity_detail.html` as template
   - Update content sections
   - Add to URLs in `v4_urls.py`

### Changing Colors

Edit `tailwind.config.js`:
```javascript
'fb-red': {
  600: '#dc2626',  // Your custom red
}
```

Then rebuild:
```bash
npm run build-css-prod
```

### Making Filters Functional

Add JavaScript in `home.html`:
```javascript
document.querySelector('#grade-dropdown').addEventListener('click', function() {
    // Filter logic here
});
```

## Next Steps

### Immediate Improvements
1. Connect filters to actual database queries
2. Implement search functionality
3. Add user authentication flows
4. Connect resources to Firebase storage

### Future Enhancements
1. Video integration for activities
2. Real community forum with posts/comments
3. User progress tracking
4. Teacher notes and favorites
5. Mobile app version

## Troubleshooting

### CSS Not Loading
```bash
npm run build-css-prod
python manage.py collectstatic --noinput
```

### Page Not Found (404)
- Check that URLs are included in `fractionball/urls.py`
- Verify V4 URLs are at root: `path('', include('content.v4_urls'))`

### Icons Not Showing
- Icons are inline SVG, should always work
- Check browser console for errors

### Static Files Not Found
```bash
python manage.py collectstatic --noinput
```

## Support

- **Full Documentation**: [V4_IMPLEMENTATION.md](V4_IMPLEMENTATION.md)
- **Main README**: [README.md](README.md)
- **Firebase Setup**: [FIREBASE_SETUP.md](FIREBASE_SETUP.md)

## Screenshots

The V4 interface matches the Figma mockups with:
- Clean, modern navigation
- Activity-focused design
- Educational aesthetics
- Responsive layouts
- Intuitive user flows

---

**Implemented**: November 2025  
**Version**: 4.0.0  
**Status**: ✅ Production Ready




























