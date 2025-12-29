/**
 * Moderation Actions
 * Helper functions for community moderation
 * These can be used with FireCMS entity callbacks or custom components
 */

import { CommunityPost } from "../collections/communityPosts";

/**
 * Flag a post for review
 */
export async function flagPost(
  _postId: string, 
  _userId: string,
  reason?: string
): Promise<Partial<CommunityPost>> {
  return {
    isFlagged: true,
    status: "flagged",
    flaggedAt: new Date(),
    flagReason: reason,
  };
}

/**
 * Approve/unflag a post
 */
export async function approvePost(
  _postId: string,
  _moderatorId: string
): Promise<Partial<CommunityPost>> {
  return {
    isFlagged: false,
    status: "active",
    moderatedAt: new Date(),
    moderationNotes: "Approved by moderator",
  };
}

/**
 * Delete/hide a post (soft delete)
 */
export async function deletePost(
  _postId: string,
  _moderatorId: string,
  reason?: string
): Promise<Partial<CommunityPost>> {
  return {
    status: "deleted",
    moderatedAt: new Date(),
    moderationNotes: reason || "Deleted by moderator",
  };
}

/**
 * Pin/Unpin a post
 */
export function togglePin(isPinned: boolean): Partial<CommunityPost> {
  return {
    isPinned: !isPinned,
  };
}
