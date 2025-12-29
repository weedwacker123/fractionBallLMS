/**
 * Bulk User Upload Action
 * CSV upload for mass user creation (critical for district onboarding per TRD)
 */

import { doc, setDoc, getFirestore } from "firebase/firestore";
import type { FirebaseApp } from "firebase/app";

export interface BulkUserData {
  email: string;
  displayName: string;
  role: "admin" | "content_manager" | "teacher";
  districtId?: string;
  schoolName?: string;
}

export interface BulkUploadResult {
  success: boolean;
  totalProcessed: number;
  successCount: number;
  failedCount: number;
  errors: { email: string; error: string }[];
}

/**
 * Parse CSV content into user data objects
 */
export function parseCSV(csvContent: string): BulkUserData[] {
  const lines = csvContent.trim().split("\n");
  
  if (lines.length < 2) {
    throw new Error("CSV must have a header row and at least one data row");
  }

  // Parse header
  const header = lines[0].split(",").map((h) => h.trim().toLowerCase());
  
  // Validate required columns
  const requiredColumns = ["email", "displayname"];
  for (const col of requiredColumns) {
    if (!header.includes(col)) {
      throw new Error(`Missing required column: ${col}`);
    }
  }

  // Parse data rows
  const users: BulkUserData[] = [];
  
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue; // Skip empty lines

    const values = line.split(",").map((v) => v.trim());
    
    const user: BulkUserData = {
      email: values[header.indexOf("email")] || "",
      displayName: values[header.indexOf("displayname")] || "",
      role: (values[header.indexOf("role")] as BulkUserData["role"]) || "teacher",
      districtId: values[header.indexOf("districtid")] || undefined,
      schoolName: values[header.indexOf("schoolname")] || undefined,
    };

    // Validate email
    if (!user.email || !user.email.includes("@")) {
      throw new Error(`Invalid email on row ${i + 1}: ${user.email}`);
    }

    // Validate role
    if (!["admin", "content_manager", "teacher"].includes(user.role)) {
      user.role = "teacher"; // Default to teacher if invalid
    }

    users.push(user);
  }

  return users;
}

/**
 * Generate CSV template for bulk user upload
 */
export function generateCSVTemplate(): string {
  return `email,displayName,role,districtId,schoolName
teacher1@school.com,John Smith,teacher,district-123,Lincoln Elementary
teacher2@school.com,Jane Doe,teacher,district-123,Lincoln Elementary
admin@school.com,Admin User,content_manager,district-123,Lincoln Elementary`;
}

/**
 * Process bulk user upload
 * Note: In production, this should be done server-side via Cloud Functions
 * This client-side implementation is for demonstration purposes
 */
export async function processBulkUpload(
  users: BulkUserData[],
  firebaseApp: FirebaseApp
): Promise<BulkUploadResult> {
  const db = getFirestore(firebaseApp);
  const result: BulkUploadResult = {
    success: true,
    totalProcessed: users.length,
    successCount: 0,
    failedCount: 0,
    errors: [],
  };

  for (const userData of users) {
    try {
      // Create Firestore document for user
      // Note: Firebase Auth user creation should be done via Cloud Functions
      // for security. This creates the Firestore user document.
      const userDoc = {
        email: userData.email,
        displayName: userData.displayName,
        role: userData.role,
        districtId: userData.districtId || null,
        schoolName: userData.schoolName || null,
        authProvider: "email",
        isActive: true,
        loginCount: 0,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      // Use email hash as document ID for consistency
      const userId = btoa(userData.email).replace(/[^a-zA-Z0-9]/g, "");
      const userRef = doc(db, "users", userId);
      
      await setDoc(userRef, userDoc);
      
      result.successCount++;
    } catch (error: unknown) {
      result.failedCount++;
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      result.errors.push({
        email: userData.email,
        error: errorMessage,
      });
    }
  }

  result.success = result.failedCount === 0;
  return result;
}

/**
 * Validate CSV content before processing
 */
export function validateCSV(csvContent: string): { valid: boolean; error?: string } {
  try {
    const users = parseCSV(csvContent);
    
    if (users.length === 0) {
      return { valid: false, error: "No valid user data found in CSV" };
    }

    if (users.length > 1000) {
      return { valid: false, error: "Maximum 1000 users per upload" };
    }

    // Check for duplicate emails
    const emails = users.map((u) => u.email.toLowerCase());
    const duplicates = emails.filter((email, index) => emails.indexOf(email) !== index);
    
    if (duplicates.length > 0) {
      return { valid: false, error: `Duplicate emails found: ${duplicates.join(", ")}` };
    }

    return { valid: true };
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "Unknown error";
    return { valid: false, error: errorMessage };
  }
}
