import { buildCollection, buildProperty, EntityReference } from "@firecms/core";

/**
 * Taxonomies Collection
 * Hierarchical tag system for organizing content
 * Supports topics, court types, grade levels, and standards
 */

// Taxonomy type enum
const taxonomyTypeValues = {
  topic: "Topic",
  court: "Court Type",
  grade: "Grade Level",
  standard: "Standard",
};

export interface TaxonomyValue {
  key: string;
  label: string;
  description?: string;
  color?: string;
}

export interface Taxonomy {
  name: string;
  type: string;
  parentId?: EntityReference;
  values: TaxonomyValue[];
  hierarchical: boolean;
  displayOrder: number;
  active: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export const taxonomiesCollection = buildCollection<Taxonomy>({
  id: "taxonomies",
  name: "Taxonomies",
  singularName: "Taxonomy",
  path: "taxonomies",
  icon: "AccountTree",
  group: "Configuration",
  description: "Manage hierarchical tag systems (topics → subtopics, courts → sub-courts)",

  // Only admins can manage taxonomies
  permissions: ({ authController }) => ({
    read: true,
    edit: authController.user?.email?.includes("admin") ?? false,
    create: authController.user?.email?.includes("admin") ?? false,
    delete: authController.user?.email?.includes("admin") ?? false,
  }),

  properties: {
    name: buildProperty({
      name: "Taxonomy Name",
      dataType: "string",
      validation: { required: true, min: 2, max: 100 },
      description: "Name of the taxonomy (e.g., 'Math Topics', 'Court Types')",
    }),

    type: buildProperty({
      name: "Taxonomy Type",
      dataType: "string",
      enumValues: taxonomyTypeValues,
      validation: { required: true },
      description: "Type of taxonomy",
    }),

    parentId: buildProperty({
      name: "Parent Taxonomy",
      dataType: "reference",
      path: "taxonomies",
      description: "Parent taxonomy for hierarchical organization",
    }),

    values: buildProperty({
      name: "Values",
      dataType: "array",
      description: "Taxonomy values/options",
      of: {
        dataType: "map",
        properties: {
          key: {
            name: "Key",
            dataType: "string",
            validation: { required: true },
            description: "Internal key (e.g., 'fractions')",
          },
          label: {
            name: "Display Label",
            dataType: "string",
            validation: { required: true },
            description: "Display name (e.g., 'Fractions')",
          },
          description: {
            name: "Description",
            dataType: "string",
            multiline: true,
          },
          color: {
            name: "Color",
            dataType: "string",
            description: "Hex color code for UI (e.g., #ef4444)",
          },
        },
      },
    }),

    hierarchical: buildProperty({
      name: "Supports Hierarchy",
      dataType: "boolean",
      description: "Whether this taxonomy supports parent-child relationships",
    }),

    displayOrder: buildProperty({
      name: "Display Order",
      dataType: "number",
      validation: { required: true, min: 0 },
      description: "Order in which to display this taxonomy",
    }),

    active: buildProperty({
      name: "Active",
      dataType: "boolean",
      description: "Whether this taxonomy is active and visible",
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
