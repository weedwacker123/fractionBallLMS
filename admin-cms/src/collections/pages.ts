import { buildCollection, buildProperty, EntityReference } from "@firecms/core";

/**
 * Pages Collection
 * Custom pages with HTML passthrough support
 * Per TRD: HTML passthrough confirmed - paste HTML directly
 */

// Menu location enum
const menuLocationValues = {
  header: "Header Menu",
  footer: "Footer Menu",
  none: "No Menu",
};

// Status enum
const statusValues = {
  draft: "Draft",
  published: "Published",
};

export interface Page {
  title: string;
  slug: string;
  content: string;
  menuLocation: string;
  displayOrder: number;
  status: string;
  metaTitle?: string;
  metaDescription?: string;
  createdBy?: EntityReference;
  createdAt: Date;
  updatedAt: Date;
}

export const pagesCollection = buildCollection<Page>({
  id: "pages",
  name: "Pages",
  singularName: "Page",
  path: "pages",
  icon: "Description",
  group: "Content",
  description: "Create custom pages - paste HTML directly for raw HTML support",

  permissions: ({ authController }) => ({
    read: true,
    edit: true,
    create: true,
    delete: authController.user?.email?.includes("admin") ?? false,
  }),

  properties: {
    title: buildProperty({
      name: "Page Title",
      dataType: "string",
      validation: { required: true, min: 2, max: 200 },
      description: "Title of the page",
    }),

    slug: buildProperty({
      name: "URL Slug",
      dataType: "string",
      validation: {
        required: true,
        matches: /^[a-z0-9-]+$/,
      },
      description: "URL-friendly identifier (e.g., 'about-us'). Use lowercase letters, numbers, and hyphens only.",
    }),

    content: buildProperty({
      name: "Page Content",
      dataType: "string",
      multiline: true,
      columnWidth: 400,
      description: "Paste HTML directly - will render as-is. Supports raw HTML passthrough.",
    }),

    menuLocation: buildProperty({
      name: "Menu Location",
      dataType: "string",
      enumValues: menuLocationValues,
      validation: { required: true },
      description: "Where to display this page in navigation",
    }),

    displayOrder: buildProperty({
      name: "Display Order",
      dataType: "number",
      validation: { required: true, min: 0 },
      description: "Order in menu (lower numbers appear first)",
    }),

    status: buildProperty({
      name: "Status",
      dataType: "string",
      enumValues: statusValues,
      validation: { required: true },
      description: "Publication status",
    }),

    metaTitle: buildProperty({
      name: "Meta Title",
      dataType: "string",
      description: "SEO meta title (optional)",
    }),

    metaDescription: buildProperty({
      name: "Meta Description",
      dataType: "string",
      multiline: true,
      description: "SEO meta description (optional)",
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
