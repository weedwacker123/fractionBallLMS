import { buildCollection, buildProperty, EntityReference } from "@firecms/core";

/**
 * Resources Collection
 * Non-video resources like PDFs, PowerPoints, Word docs
 */

// Resource type enum
const resourceTypeValues = {
  pdf: "PDF Document",
  pptx: "PowerPoint Presentation",
  docx: "Word Document",
  xlsx: "Excel Spreadsheet",
  other: "Other",
};

export interface Resource {
  title: string;
  caption?: string;
  type: string;
  fileUrl: string;
  fileName?: string;
  fileSize?: number;
  mimeType?: string;
  uploadedBy?: EntityReference;
  uploadedAt: Date;
}

export const resourcesCollection = buildCollection<Resource>({
  id: "resources",
  name: "Resources",
  singularName: "Resource",
  path: "resources",
  icon: "Folder",
  group: "Media",
  description: "PDFs, PowerPoints, Word documents, and other resources",

  permissions: ({ authController }) => ({
    read: true,
    edit: true,
    create: true,
    delete: authController.user?.email?.includes("admin") ?? false,
  }),

  properties: {
    title: buildProperty({
      name: "Resource Title",
      dataType: "string",
      validation: { required: true, min: 3, max: 200 },
      description: "Title of the resource",
    }),

    caption: buildProperty({
      name: "Caption",
      dataType: "string",
      multiline: true,
      description: "Description or caption for the resource",
    }),

    type: buildProperty({
      name: "Resource Type",
      dataType: "string",
      enumValues: resourceTypeValues,
      validation: { required: true },
      description: "Type of resource file",
    }),

    fileUrl: buildProperty({
      name: "Resource File",
      dataType: "string",
      validation: { required: true },
      storage: {
        storagePath: "resources",
        acceptedFiles: [
          "application/pdf",
          "application/vnd.ms-powerpoint",
          "application/vnd.openxmlformats-officedocument.presentationml.presentation",
          "application/msword",
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          "application/vnd.ms-excel",
          "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ],
        maxSize: 50 * 1024 * 1024, // 50MB
        metadata: {
          cacheControl: "max-age=3600",
        },
      },
      description: "Upload resource file (max 50MB)",
    }),

    fileName: buildProperty({
      name: "Original File Name",
      dataType: "string",
      readOnly: true,
      description: "Original name of the uploaded file",
    }),

    fileSize: buildProperty({
      name: "File Size (bytes)",
      dataType: "number",
      readOnly: true,
      description: "File size in bytes",
    }),

    mimeType: buildProperty({
      name: "MIME Type",
      dataType: "string",
      readOnly: true,
      description: "File MIME type",
    }),

    uploadedBy: buildProperty({
      name: "Uploaded By",
      dataType: "reference",
      path: "users",
      readOnly: true,
    }),

    uploadedAt: buildProperty({
      name: "Uploaded At",
      dataType: "date",
      autoValue: "on_create",
      readOnly: true,
    }),
  },
});
