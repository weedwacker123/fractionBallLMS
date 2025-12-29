import { buildCollection, buildProperty } from "@firecms/core";

/**
 * FAQs Collection
 * Frequently Asked Questions management
 * Extensible, categorized, with drag-drop ordering support
 */

// Status enum
const statusValues = {
  draft: "Draft",
  published: "Published",
};

// Category enum
const categoryValues = {
  getting_started: "Getting Started",
  implementation: "Implementation",
  technical: "Technical Support",
  account: "Account & Access",
  content: "Content & Activities",
  community: "Community",
  other: "Other",
};

export interface FAQ {
  question: string;
  answer: string;
  category: string;
  displayOrder: number;
  status: string;
  helpful?: number;
  notHelpful?: number;
  createdAt: Date;
  updatedAt: Date;
}

export const faqsCollection = buildCollection<FAQ>({
  id: "faqs",
  name: "FAQs",
  singularName: "FAQ",
  path: "faqs",
  icon: "Help",
  group: "Support",
  description: "Frequently Asked Questions - categorized and ordered",

  permissions: ({ authController }) => ({
    read: true,
    edit: true,
    create: true,
    delete: authController.user?.email?.includes("admin") ?? false,
  }),

  // Initial sort by category then displayOrder
  initialSort: ["category", "asc"],

  properties: {
    question: buildProperty({
      name: "Question",
      dataType: "string",
      validation: { required: true, min: 10, max: 500 },
      description: "The FAQ question",
    }),

    answer: buildProperty({
      name: "Answer",
      dataType: "string",
      multiline: true,
      markdown: true,
      validation: { required: true },
      description: "The answer (supports Markdown/HTML)",
    }),

    category: buildProperty({
      name: "Category",
      dataType: "string",
      validation: { required: true },
      enumValues: categoryValues,
      description: "FAQ category for organization",
    }),

    displayOrder: buildProperty({
      name: "Display Order",
      dataType: "number",
      validation: { required: true, min: 0 },
      description: "Order within category (lower numbers first)",
    }),

    status: buildProperty({
      name: "Status",
      dataType: "string",
      enumValues: statusValues,
      validation: { required: true },
      description: "Publication status",
    }),

    helpful: buildProperty({
      name: "Helpful Count",
      dataType: "number",
      readOnly: true,
      description: "Number of users who found this helpful",
    }),

    notHelpful: buildProperty({
      name: "Not Helpful Count",
      dataType: "number",
      readOnly: true,
      description: "Number of users who did not find this helpful",
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
