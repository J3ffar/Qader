import { CommunityReply } from "@/types/api/community.types";

export interface NestedReply extends CommunityReply {
  childReplies: NestedReply[];
}

export function buildReplyTree(replies: CommunityReply[]): NestedReply[] {
  const replyMap = new Map<number, NestedReply>();
  const rootReplies: NestedReply[] = [];

  // First pass: create a map of all replies and initialize childReplies array
  replies.forEach((reply) => {
    replyMap.set(reply.id, { ...reply, childReplies: [] });
  });

  // Second pass: link children to their parents
  replyMap.forEach((nestedReply) => {
    if (nestedReply.parent_reply_read_id) {
      const parent = replyMap.get(nestedReply.parent_reply_read_id);
      if (parent) {
        // To ensure chronological order, we can push or unshift
        parent.childReplies.push(nestedReply);
      } else {
        // This case handles children whose parents might not be on the current page
        rootReplies.push(nestedReply);
      }
    } else {
      rootReplies.push(nestedReply);
    }
  });

  // Optional: Sort child replies within each parent if needed
  // rootReplies.forEach(reply => reply.childReplies.sort((a,b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()));

  return rootReplies;
}
