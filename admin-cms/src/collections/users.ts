import { buildCollection, buildProperty, EntityReference } from "@firecms/core";

/**
 * Users Collection
 * User management with role-based access
 * Per TRD: Admin can create, delete, change roles, bulk upload via CSV
 */

// User role enum
const roleValues = {
  admin: "Admin",
  content_manager: "Content Manager",
  teacher: "Teacher",
};

// Auth provider enum
const authProviderValues = {
  google: "Google",
  microsoft: "Microsoft",
  email: "Email/Password",
};

export interface User {
  email: string;
  displayName: string;
  role: string;
  customRoleId?: EntityReference;
  authProvider: string;
  districtId?: string;
  schoolName?: string;
  phone?: string;
  avatar?: string;
  isActive: boolean;
  lastLogin?: Date;
  loginCount: number;
  createdAt: Date;
  updatedAt: Date;
}

export const usersCollection = buildCollection<User>({
  id: "users",
  name: "Users",
  singularName: "User",
  path: "users",
  icon: "People",
  group: "User Management",
  description: "Manage users, roles, and access permissions",

  // Only admins can fully manage users
  permissions: ({ authController }) => ({
    read: true,
    edit: authController.user?.email?.includes("admin") ?? false,
    create: authController.user?.email?.includes("admin") ?? false,
    delete: authController.user?.email?.includes("admin") ?? false,
  }),

  properties: {
    email: buildProperty({
      name: "Email",
      dataType: "string",
      validation: {
        required: true,
        email: true,
      },
      description: "User's email address",
    }),

    displayName: buildProperty({
      name: "Display Name",
      dataType: "string",
      validation: { required: true, min: 2, max: 100 },
      description: "User can edit this in their profile",
    }),

    role: buildProperty({
      name: "Role",
      dataType: "string",
      enumValues: roleValues,
      validation: { required: true },
      description: "User role determines access permissions",
    }),

    customRoleId: buildProperty({
      name: "Custom Role",
      dataType: "reference",
      path: "roles",
      description: "Optional custom role (for future expansion)",
    }),

    authProvider: buildProperty({
      name: "Auth Provider",
      dataType: "string",
      enumValues: authProviderValues,
      validation: { required: true },
      description: "How the user logs in",
    }),

    districtId: buildProperty({
      name: "District ID",
      dataType: "string",
      description: "School district identifier",
    }),

    schoolName: buildProperty({
      name: "School Name",
      dataType: "string",
      description: "User's school",
    }),

    phone: buildProperty({
      name: "Phone",
      dataType: "string",
      description: "Contact phone number",
    }),

    avatar: buildProperty({
      name: "Avatar",
      dataType: "string",
      storage: {
        storagePath: "avatars",
        acceptedFiles: ["image/*"],
        maxSize: 1 * 1024 * 1024, // 1MB
      },
      description: "User profile picture",
    }),

    isActive: buildProperty({
      name: "Active",
      dataType: "boolean",
      description: "Whether the user account is active",
    }),

    lastLogin: buildProperty({
      name: "Last Login",
      dataType: "date",
      readOnly: true,
      description: "Last login timestamp",
    }),

    loginCount: buildProperty({
      name: "Login Count",
      dataType: "number",
      readOnly: true,
      description: "Total number of logins",
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
