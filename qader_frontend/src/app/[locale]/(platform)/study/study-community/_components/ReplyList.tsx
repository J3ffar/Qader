"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { getRepliesForPost } from "@/services/community.service";
import { queryKeys } from "@/constants/queryKeys";
import { CommunityReply } from "@/types/api/community.types";
import { Loader2 } from "lucide-react";
import { ReplyCard } from "./ReplyCard";
import { Button } from "@/components/ui/button";

interface ReplyListProps {
  postId: number;
  isPostClosed: boolean;
}

export function ReplyList({ postId, isPostClosed }: ReplyListProps) {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
  } = useInfiniteQuery({
    queryKey: queryKeys.community.postDetails.replies(postId),
    queryFn: getRepliesForPost,
    initialPageParam: "1",
    getNextPageParam: (lastPage) => {
      if (lastPage.next) {
        const url = new URL(lastPage.next);
        return url.searchParams.get("page");
      }
      return undefined;
    },
  });

  if (isLoading) {
    return (
      <div className="flex justify-center py-4">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }
  if (isError) {
    return (
      <p className="text-center text-destructive text-sm">
        فشل في تحميل الردود.
      </p>
    );
  }

  const replies = data?.pages.flatMap((page) => page.results) ?? [];

  return (
    <div className="space-y-4 pt-4">
      {replies.map((reply: CommunityReply) => (
        <ReplyCard key={reply.id} reply={reply} isPostClosed={isPostClosed} />
      ))}

      {hasNextPage && (
        <Button
          variant="link"
          className="p-0 h-auto"
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? "جاري التحميل..." : "عرض المزيد من الردود"}
        </Button>
      )}
    </div>
  );
}
