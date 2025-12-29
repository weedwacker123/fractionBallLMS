import { buildCollection, buildProperty, EntityReference } from "@firecms/core";

/**
 * Videos Collection
 * Video content assets for the media library
 */

export interface Video {
  title: string;
  description?: string;
  fileUrl: string;
  thumbnailUrl?: string;
  duration?: number;
  fileSize?: number;
  uploadedBy?: EntityReference;
  uploadedAt: Date;
}

export const videosCollection = buildCollection<Video>({
  id: "videos",
  name: "Videos",
  singularName: "Video",
  path: "videos",
  icon: "VideoLibrary",
  group: "Media",
  description: "Video content library for activities",

  permissions: ({ authController }) => ({
    read: true,
    edit: true,
    create: true,
    delete: authController.user?.email?.includes("admin") ?? false,
  }),

  properties: {
    title: buildProperty({
      name: "Video Title",
      dataType: "string",
      validation: { required: true, min: 3, max: 200 },
      description: "Title of the video",
    }),

    description: buildProperty({
      name: "Description",
      dataType: "string",
      multiline: true,
      description: "Detailed description of the video content",
    }),

    fileUrl: buildProperty({
      name: "Video File",
      dataType: "string",
      validation: { required: true },
      storage: {
        storagePath: "videos",
        acceptedFiles: ["video/mp4", "video/webm", "video/quicktime"],
        maxSize: 500 * 1024 * 1024, // 500MB
        metadata: {
          cacheControl: "max-age=3600",
        },
      },
      description: "Upload MP4 video file (max 500MB)",
    }),

    thumbnailUrl: buildProperty({
      name: "Thumbnail",
      dataType: "string",
      storage: {
        storagePath: "thumbnails/videos",
        acceptedFiles: ["image/*"],
        maxSize: 2 * 1024 * 1024, // 2MB
        metadata: {
          cacheControl: "max-age=86400",
        },
      },
      description: "Video thumbnail image",
    }),

    duration: buildProperty({
      name: "Duration (seconds)",
      dataType: "number",
      description: "Video duration in seconds",
      validation: { min: 0 },
    }),

    fileSize: buildProperty({
      name: "File Size (bytes)",
      dataType: "number",
      description: "File size in bytes",
      readOnly: true,
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
