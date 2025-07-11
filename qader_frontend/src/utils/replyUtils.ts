import { CommunityReply } from "@/types/api/community.types";

export interface NestedReply extends CommunityReply {
  childReplies: NestedReply[];
}

export function buildReplyTree(replies: CommunityReply[]): NestedReply[] {
  // Sort all replies by newest first before building the tree
  const sortedReplies = [...replies].sort(
    (a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const replyMap = new Map<number, NestedReply>();
  const rootReplies: NestedReply[] = [];

  sortedReplies.forEach((reply) => {
    replyMap.set(reply.id, { ...reply, childReplies: [] });
  });

  replyMap.forEach((nestedReply) => {
    if (nestedReply.parent_reply_read_id) {
      const parent = replyMap.get(nestedReply.parent_reply_read_id);
      if (parent) {
        // Since the initial array is sorted newest to oldest, we unshift to maintain that order in children.
        parent.childReplies.unshift(nestedReply);
      } else {
        rootReplies.push(nestedReply);
      }
    } else {
      rootReplies.push(nestedReply);
    }
  });

  return rootReplies;
}
