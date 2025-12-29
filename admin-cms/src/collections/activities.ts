import { buildCollection, buildProperty, EntityReference } from "@firecms/core";

/**
 * Activities Collection
 * Main educational activities with full taxonomy support
 * Required fields per TRD: title, videos (with title/caption), resources (with title/caption), lessonPdf
 */

// Grade level enum
const gradeLevelValues = {
  0: "Kindergarten",
  1: "Grade 1",
  2: "Grade 2",
  3: "Grade 3",
  4: "Grade 4",
  5: "Grade 5",
  6: "Grade 6",
  7: "Grade 7",
  8: "Grade 8",
  9: "Grade 9",
  10: "Grade 10",
  11: "Grade 11",
  12: "Grade 12",
};

// Status values
const statusValues = {
  draft: "Draft",
  published: "Published",
  archived: "Archived",
};

// Video types
const videoTypeValues = {
  prerequisite: "Prerequisite",
  instructional: "Instructional",
  related: "Related",
};

// Resource types
const resourceTypeValues = {
  pdf: "PDF",
  pptx: "PowerPoint",
  docx: "Word Doc",
};

// Activity type interface
export interface Activity {
  title: string;
  description?: string;
  gradeLevel: number[];
  tags: string[];
  taxonomy: {
    topic?: string;
    subtopic?: string;
    courtType?: string;
    standard?: string;
  };
  prerequisiteActivities?: EntityReference[];
  videos: {
    videoId: EntityReference;
    title: string;
    caption: string;
    type: string;
    displayOrder: number;
  }[];
  resources: {
    resourceId: EntityReference;
    title: string;
    caption: string;
    type: string;
  }[];
  lessonPdf: string;
  thumbnailUrl?: string;
  status: string;
  createdBy?: EntityReference;
  createdAt: Date;
  updatedAt: Date;
}

export const activitiesCollection = buildCollection<Activity>({
  id: "activities",
  name: "Activities",
  singularName: "Activity",
  path: "activities",
  icon: "SportsBasketball",
  group: "Content",
  description: "Educational activities with videos, resources, and lesson plans",
  
  permissions: ({ authController }) => ({
    read: true,
    edit: true,
    create: true,
    delete: authController.user?.email?.includes("admin") ?? false,
  }),

  properties: {
    title: buildProperty({
      name: "Activity Title",
      dataType: "string",
      validation: { required: true, min: 3, max: 200 },
      description: "The title of this activity",
    }),

    description: buildProperty({
      name: "Description",
      dataType: "string",
      multiline: true,
      markdown: true,
      description: "Detailed description of the activity (supports Markdown)",
    }),

    gradeLevel: buildProperty({
      name: "Grade Levels",
      dataType: "array",
      of: {
        dataType: "number",
        enumValues: gradeLevelValues,
      },
      validation: { required: true, min: 1 },
      description: "Target grade levels for this activity",
    }),

    tags: buildProperty({
      name: "Tags",
      dataType: "array",
      of: {
        dataType: "string",
      },
      description: "Tags for categorization (e.g., fractions, decimals, court-1)",
    }),

    taxonomy: buildProperty({
      name: "Taxonomy",
      dataType: "map",
      description: "Hierarchical organization of the activity",
      properties: {
        topic: {
          name: "Topic",
          dataType: "string",
          description: "Primary topic (e.g., fractions)",
        },
        subtopic: {
          name: "Subtopic",
          dataType: "string",
          description: "Subtopic (e.g., mixed-denominators)",
        },
        courtType: {
          name: "Court Type",
          dataType: "string",
          description: "Court type (e.g., fraction-ball-court-1)",
        },
        standard: {
          name: "Standard",
          dataType: "string",
          description: "Educational standard (e.g., CCSS.MATH.3.NF.A.1)",
        },
      },
    }),

    prerequisiteActivities: buildProperty({
      name: "Prerequisite Activities",
      dataType: "array",
      of: {
        dataType: "reference",
        path: "activities",
      },
      description: "Activities that should be completed before this one",
    }),

    videos: buildProperty({
      name: "Videos",
      dataType: "array",
      validation: { required: true, min: 1 },
      description: "Videos associated with this activity",
      of: {
        dataType: "map",
        properties: {
          videoId: {
            name: "Select Video",
            dataType: "reference",
            path: "videos",
            validation: { required: true },
          },
          title: {
            name: "Video Title",
            dataType: "string",
            validation: { required: true },
            description: "Display title for this video in the activity",
          },
          caption: {
            name: "Video Caption",
            dataType: "string",
            validation: { required: true },
            multiline: true,
            description: "Caption explaining the video's purpose",
          },
          type: {
            name: "Video Type",
            dataType: "string",
            enumValues: videoTypeValues,
            validation: { required: true },
          },
          displayOrder: {
            name: "Display Order",
            dataType: "number",
            validation: { required: true, min: 0 },
          },
        },
      },
    }),

    resources: buildProperty({
      name: "Resources",
      dataType: "array",
      validation: { required: true },
      description: "PDFs, PowerPoints, and Word docs for this activity",
      of: {
        dataType: "map",
        properties: {
          resourceId: {
            name: "Select Resource",
            dataType: "reference",
            path: "resources",
            validation: { required: true },
          },
          title: {
            name: "Resource Title",
            dataType: "string",
            validation: { required: true },
            description: "Display title for this resource",
          },
          caption: {
            name: "Resource Caption",
            dataType: "string",
            validation: { required: true },
            multiline: true,
            description: "Caption explaining the resource",
          },
          type: {
            name: "Resource Type",
            dataType: "string",
            enumValues: resourceTypeValues,
            validation: { required: true },
          },
        },
      },
    }),

    lessonPdf: buildProperty({
      name: "Lesson Plan PDF",
      dataType: "string",
      validation: { required: true },
      storage: {
        storagePath: "lesson-plans",
        acceptedFiles: ["application/pdf"],
        maxSize: 10 * 1024 * 1024, // 10MB
        metadata: {
          cacheControl: "max-age=3600",
        },
      },
      description: "Upload the lesson plan PDF (required)",
    }),

    thumbnailUrl: buildProperty({
      name: "Thumbnail Image",
      dataType: "string",
      storage: {
        storagePath: "thumbnails/activities",
        acceptedFiles: ["image/*"],
        maxSize: 2 * 1024 * 1024, // 2MB
        metadata: {
          cacheControl: "max-age=86400",
        },
      },
      description: "Activity thumbnail image",
    }),

    status: buildProperty({
      name: "Status",
      dataType: "string",
      enumValues: statusValues,
      validation: { required: true },
      description: "Publication status",
    }),

    createdBy: buildProperty({
      name: "Created By",
      dataType: "reference",
      path: "users",
      readOnly: true,
    }),

    createdAt: buildProperty({
      name: "Created At",
      dataType: "date",
      autoValue: "on_create",
      readOnly: true,
    }),

    updatedAt: buildProperty({
      name: "Updated At",
      dataType: "date",
      autoValue: "on_update",
      readOnly: true,
    }),
  },
});
