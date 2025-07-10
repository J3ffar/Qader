import getQueryClient from "@/lib/getQueryClient";
import { HydrationBoundary, dehydrate } from "@tanstack/react-query";
import { CommunityFeed } from "./_components/CommunityFeed";
import { getCommunityPosts } from "@/services/community.service";
import { queryKeys } from "@/constants/queryKeys";
import { Button } from "@/components/ui/button";
import { Filter } from "lucide-react";
import { CreatePostDialog } from "./_components/CreatePostDialog";

export default async function StudyCommunityPage() {
  const queryClient = getQueryClient();
  const initialFilters = { post_type: "discussion", ordering: "-created_at" };

  await queryClient.prefetchInfiniteQuery({
    queryKey: queryKeys.community.posts.list(initialFilters),
    queryFn: getCommunityPosts,
    initialPageParam: 1,
  });

  return (
    <div className="container mx-auto max-w-3xl py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">مجتمع الطالب</h1>
          <p className="text-muted-foreground">
            المجتمع الذي يجمعك مع زملائك لتشاركوا التجارب.
          </p>
        </div>
        <CreatePostDialog />
      </div>

      {/* Filters can be implemented here */}
      {/* <CommunityFilters /> */}

      <div className="flex justify-end mb-4">
        <Button variant="outline">
          <Filter className="ms-2 h-4 w-4" />
          تصفية
        </Button>
      </div>

      <HydrationBoundary state={dehydrate(queryClient)}>
        <CommunityFeed initialFilters={initialFilters} />
      </HydrationBoundary>
    </div>
  );
}
