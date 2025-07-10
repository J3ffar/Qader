"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { Fragment, useEffect, useRef } from "react";
import { useIntersection } from "@mantine/hooks";
import { queryKeys } from "@/constants/queryKeys";
import { getCommunityPosts } from "@/services/community.service";
import { PostSkeleton } from "./PostSkeleton";
import { PostCard } from "./PostCard";
import { CommunityPostList } from "@/types/api/community.types";
import { Loader2 } from "lucide-react";

interface CommunityFeedProps {
  initialFilters: { post_type: string; ordering: string };
}

export function CommunityFeed({ initialFilters }: CommunityFeedProps) {
  const { data, fetchNextPage, isFetchingNextPage, isLoading, isError } =
    useInfiniteQuery({
      queryKey: queryKeys.community.posts.list(initialFilters),
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
    if (entry?.isIntersecting) {
      fetchNextPage();
    }
  }, [entry, fetchNextPage]);

  const posts = data?.pages.flatMap((page) => page.results) ?? [];

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
      <div className="text-center text-destructive">
        فشل في تحميل المنشورات. حاول مرة أخرى.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {posts.map((post: CommunityPostList, i: number) => {
        if (i === posts.length - 1) {
          return (
            <div key={post.id} ref={ref}>
              <PostCard post={post} />
            </div>
          );
        }
        return <PostCard key={post.id} post={post} />;
      })}
      {isFetchingNextPage && (
        <div className="flex justify-center items-center py-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="ms-2">جاري تحميل المزيد...</p>
        </div>
      )}
      {!isFetchingNextPage && posts.length === 0 && (
        <div className="text-center text-muted-foreground py-10">
          لا توجد منشورات لعرضها.
        </div>
      )}
    </div>
  );
}
