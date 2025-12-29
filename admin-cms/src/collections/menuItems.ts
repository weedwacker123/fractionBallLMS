import { buildCollection, buildProperty, EntityReference } from "@firecms/core";

/**
 * Menu Items Collection
 * Dynamic navigation management with submenu support
 * Per TRD: Menu administration is a critical requirement
 */

// Menu item type enum
const menuTypeValues = {
  page: "Page",
  external: "External Link",
  activity_category: "Activity Category",
};

// Menu location enum
const locationValues = {
  header: "Header",
  footer: "Footer",
};

export interface MenuItem {
  label: string;
  url: string;
  type: string;
  parentId?: EntityReference;
  location: string;
  displayOrder: number;
  openInNewTab: boolean;
  active: boolean;
  icon?: string;
  createdAt: Date;
  updatedAt: Date;
}

export const menuItemsCollection = buildCollection<MenuItem>({
  id: "menuItems",
  name: "Menu Items",
  singularName: "Menu Item",
  path: "menuItems",
  icon: "Menu",
  group: "Configuration",
  description: "Manage navigation menus and submenus",

  // Only admins can manage menus
  permissions: ({ authController }) => ({
    read: true,
    edit: authController.user?.email?.includes("admin") ?? false,
    create: authController.user?.email?.includes("admin") ?? false,
    delete: authController.user?.email?.includes("admin") ?? false,
  }),

  properties: {
    label: buildProperty({
      name: "Menu Label",
      dataType: "string",
      validation: { required: true, min: 1, max: 50 },
      description: "Text displayed in the menu",
    }),

    url: buildProperty({
      name: "URL",
      dataType: "string",
      validation: { required: true },
      description: "Internal path (e.g., /about) or external URL (e.g., https://...)",
    }),

    type: buildProperty({
      name: "Link Type",
      dataType: "string",
      enumValues: menuTypeValues,
      validation: { required: true },
      description: "Type of menu link",
    }),

    parentId: buildProperty({
      name: "Parent Menu Item",
      dataType: "reference",
      path: "menuItems",
      description: "For creating submenus - select the parent menu item",
    }),

    location: buildProperty({
      name: "Menu Location",
      dataType: "string",
      enumValues: locationValues,
      validation: { required: true },
      description: "Where this menu item appears",
    }),

    displayOrder: buildProperty({
      name: "Display Order",
      dataType: "number",
      validation: { required: true, min: 0 },
      description: "Order within the menu (lower numbers first)",
    }),

    openInNewTab: buildProperty({
      name: "Open in New Tab",
      dataType: "boolean",
      description: "Open link in a new browser tab",
    }),

    active: buildProperty({
      name: "Active",
      dataType: "boolean",
      description: "Whether this menu item is visible",
    }),

    icon: buildProperty({
      name: "Icon",
      dataType: "string",
      description: "Optional icon name (e.g., 'home', 'book', 'users')",
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
