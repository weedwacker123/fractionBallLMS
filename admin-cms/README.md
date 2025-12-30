# Fraction Ball Admin CMS

FireCMS-based admin interface for managing Fraction Ball LMS content in Firestore.

## Features

### Content Management
- **Activities** - Create and manage educational activities with videos, resources, and lesson plans
- **Videos** - Upload and organize video content (MP4, up to 500MB)
- **Resources** - Manage PDFs, PowerPoints, Word documents (up to 50MB)

### Taxonomy & Organization
- **Taxonomies** - Hierarchical tag system for topics, court types, standards
- **Pages** - Custom pages with raw HTML passthrough
- **Menu Items** - Dynamic navigation management with submenu support

### Support & Community
- **FAQs** - Manage frequently asked questions by category
- **Community Posts** - Forum moderation with flagging system
- **Comments** - Nested comment management

### User Management
- **Users** - Role-based user management (Admin, Content Manager, Teacher)
- **Bulk Upload** - CSV import for mass user creation (up to 1000 users)

## Getting Started

### Prerequisites
- Node.js 18+
- Firebase project with Firestore and Storage enabled

### Installation

```bash
# Navigate to admin-cms directory
cd admin-cms

# Install dependencies
npm install

# Start development server
npm run dev
```

The admin interface will be available at `http://localhost:5173`

### Environment Setup

The Firebase configuration is already set in `src/firebase-config.ts`. For production, update with your Firebase project credentials.

### Deploying to Firebase Hosting

```bash
# Build for production
npm run build

# Deploy (requires Firebase CLI)
firebase deploy --only hosting:admin
```

## Collection Schemas

### Activities
```typescript
{
  title: string;           // Required
  description: string;     // Markdown supported
  gradeLevel: number[];    // K-12 (0-12)
  tags: string[];
  taxonomy: {
    topic: string;
    subtopic: string;
    courtType: string;
    standard: string;
  };
  videos: [{               // Required
    videoId: Reference;
    title: string;         // Required
    caption: string;       // Required
    type: 'prerequisite' | 'instructional' | 'related';
    displayOrder: number;
  }];
  resources: [{            // Required
    resourceId: Reference;
    title: string;         // Required
    caption: string;       // Required
    type: 'pdf' | 'pptx' | 'docx';
  }];
  lessonPdf: string;       // Required - Firebase Storage URL
  status: 'draft' | 'published' | 'archived';
}
```

### Community Posts (with Moderation)
```typescript
{
  authorId: Reference;
  title: string;
  content: string;          // Markdown
  category: 'question' | 'discussion' | 'resource_share' | 'announcement';
  isPinned: boolean;
  isFlagged: boolean;       // For moderation
  flagReason: string;
  status: 'active' | 'flagged' | 'deleted';
  moderatedBy: Reference;
  moderationNotes: string;
}
```

### Users
```typescript
{
  email: string;
  displayName: string;
  role: 'admin' | 'content_manager' | 'teacher';
  authProvider: 'google' | 'microsoft' | 'email';
  districtId: string;
  schoolName: string;
  isActive: boolean;
}
```

## User Roles & Permissions

| Role | Activities | Videos | Resources | Pages | FAQs | Users | Taxonomies | Menu Items |
|------|------------|--------|-----------|-------|------|-------|------------|------------|
| Admin | Full | Full | Full | Full | Full | Full | Full | Full |
| Content Manager | CRUD | CRUD | CRUD | CRUD | CRUD | Read | Read | Read |
| Teacher | Read | Read | Read | Read | Read | Own | - | - |

## Bulk User Upload

The admin interface includes a bulk user upload feature for district onboarding:

1. Download the CSV template
2. Fill in user data (email, displayName, role, districtId, schoolName)
3. Upload CSV (max 1000 users per upload)
4. Review and confirm
5. Users are created with email/password auth

## Firebase Security Rules

Deploy the included security rules:

```bash
# Deploy Firestore rules
firebase deploy --only firestore:rules

# Deploy Storage rules
firebase deploy --only storage:rules
```

## Development

### Project Structure
```
admin-cms/
├── src/
│   ├── collections/      # FireCMS collection schemas
│   │   ├── activities.ts
│   │   ├── videos.ts
│   │   ├── resources.ts
│   │   ├── taxonomies.ts
│   │   ├── pages.ts
│   │   ├── menuItems.ts
│   │   ├── faqs.ts
│   │   ├── communityPosts.ts
│   │   └── users.ts
│   ├── actions/          # Custom actions
│   │   ├── moderationActions.ts
│   │   └── bulkUserUpload.ts
│   ├── views/            # Custom views
│   │   └── BulkUserUploadView.tsx
│   ├── App.tsx           # Main FireCMS app
│   └── firebase-config.ts
├── public/
│   ├── logo.svg
│   └── favicon.svg
├── firestore.rules
├── storage.rules
└── package.json
```

### Building for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

## License

Private - Fraction Ball © 2025


