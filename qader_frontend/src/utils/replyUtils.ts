import { CommunityReply } from "@/types/api/community.types";

export interface NestedReply extends CommunityReply {
  childReplies: NestedReply[];
}

export function buildReplyTree(replies: CommunityReply[]): NestedReply[] {
  // We don't need to pre-sort the entire list. It's more efficient to sort children as they are added.
  const replyMap = new Map<number, NestedReply>();
  const rootReplies: NestedReply[] = [];

  replies.forEach((reply) => {
    replyMap.set(reply.id, { ...reply, childReplies: [] });
  });

  // Create a new array for roots to avoid mutation issues during iteration
  const potentialRoots: NestedReply[] = [];
  replyMap.forEach((nestedReply) => {
    if (nestedReply.parent_reply_read_id) {
      const parent = replyMap.get(nestedReply.parent_reply_read_id);
      if (parent) {
        parent.childReplies.push(nestedReply);
      } else {
        potentialRoots.push(nestedReply);
      }
    } else {
      potentialRoots.push(nestedReply);
    }
  });

  // Now, sort the root replies and all child replies from newest to oldest
  const sortByDate = (a: NestedReply, b: NestedReply) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime();

  potentialRoots.forEach((reply) => {
    if (reply.childReplies.length > 1) {
      reply.childReplies.sort(sortByDate); // <-- **THE FIX**
    }
  });

  potentialRoots.sort(sortByDate);

  return potentialRoots;
}
