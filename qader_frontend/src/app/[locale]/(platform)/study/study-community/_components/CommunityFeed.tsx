"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useIntersection } from "@mantine/hooks";
import { queryKeys } from "@/constants/queryKeys";
import { getCommunityPosts } from "@/services/community.service";
import { PostSkeleton } from "./PostSkeleton";
import { PostCard } from "./PostCard";
import { CommunityPostList } from "@/types/api/community.types";
import { Loader2 } from "lucide-react";

interface CommunityFeedProps {
  filters: { post_type: string; ordering: string };
}

export function CommunityFeed({ filters }: CommunityFeedProps) {
  const {
    data,
    fetchNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    isRefetching,
  } = useInfiniteQuery({
    queryKey: queryKeys.community.posts.list(filters),
    queryFn: getCommunityPosts,
    initialPageParam: "1",
    getNextPageParam: (lastPage) => {
      if (lastPage.next) {
        const url = new URL(lastPage.next);
        return url.searchParams.get("page");
      }
      return undefined;
    },
  });

  const lastPostRef = useRef<HTMLElement>(null);
  const { ref, entry } = useIntersection({
    root: lastPostRef.current,
    threshold: 1,
  });

  useEffect(() => {
    if (entry?.isIntersecting && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [entry, fetchNextPage, isFetchingNextPage]);

  const posts = data?.pages.flatMap((page) => page.results) ?? [];

  // Show skeleton on initial load for a new filter set
  if (isLoading) {
    return (
      <div className="space-y-6">
        <PostSkeleton />
        <PostSkeleton />
        <PostSkeleton />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center text-destructive py-10">
        فشل في تحميل المنشورات. حاول مرة أخرى.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {posts.map((post: CommunityPostList, i: number) => {
        const isLastPost = i === posts.length - 1;
        // The optimistic update logic in PostCard requires passing the current filters to construct the correct queryKey
        return (
          <div key={post.id} ref={isLastPost ? ref : null}>
            <PostCard
              post={post}
              listQueryKey={queryKeys.community.posts.list(filters)}
            />
          </div>
        );
      })}

      {isFetchingNextPage && (
        <div className="flex justify-center items-center py-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="ms-2">جاري تحميل المزيد...</p>
        </div>
      )}

      {!isFetchingNextPage && !isLoading && posts.length === 0 && (
        <div className="text-center text-muted-foreground py-10">
          لا توجد منشورات في هذا القسم بعد.
        </div>
      )}
    </div>
  );
}
