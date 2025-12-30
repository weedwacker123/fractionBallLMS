# Fraction Ball Admin CMS - Quick Start Guide

## Getting Started

### 1. Install Dependencies
```bash
cd admin-cms
npm install
```

### 2. Start Development Server
```bash
npm run dev
```
Visit http://localhost:5173

### 3. Build for Production
```bash
npm run build
```

## Firebase Setup

### Deploy Firestore Rules
```bash
cd /path/to/fractionBallLMS
firebase deploy --only firestore:rules
```

### Deploy Storage Rules
```bash
firebase deploy --only storage:rules
```

### Deploy Admin CMS to Firebase Hosting
```bash
# First, add hosting target in Firebase console
firebase target:apply hosting admin fractionball-admin

# Then deploy
firebase deploy --only hosting:admin
```

## Collections Overview

| Collection | Description | Permissions |
|------------|-------------|-------------|
| **Activities** | Educational activities with videos & resources | Admin: Full, Content Manager: CRUD |
| **Videos** | Video content library (MP4, up to 500MB) | Admin: Full, Content Manager: CRUD |
| **Resources** | PDFs, PPTs, Word docs (up to 50MB) | Admin: Full, Content Manager: CRUD |
| **Taxonomies** | Hierarchical tags (topics, courts, grades) | Admin Only |
| **Pages** | Custom HTML pages | Admin: Full, Content Manager: CRUD |
| **Menu Items** | Navigation management | Admin Only |
| **FAQs** | Frequently Asked Questions | Admin: Full, Content Manager: CRUD |
| **Community Posts** | Forum with moderation | Admin: Full, Others: Limited |
| **Users** | User management & roles | Admin Only |

## User Roles

- **Admin**: Full access to all features
- **Content Manager**: Can create/edit content, cannot delete or manage users
- **Teacher**: Read-only access to content

## First-Time Setup

1. Log in with a Google account
2. Create your first user in the Users collection
3. Set your role to "admin"
4. Create taxonomies for topics and court types
5. Start adding activities!

## File Upload Limits

| Type | Max Size |
|------|----------|
| Videos | 500 MB |
| Resources | 50 MB |
| Lesson PDFs | 10 MB |
| Thumbnails | 2 MB |
| Avatars | 1 MB |


