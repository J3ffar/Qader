import getQueryClient from "@/lib/getQueryClient";
import { HydrationBoundary, dehydrate } from "@tanstack/react-query";
import { getCommunityPosts } from "@/services/community.service";
import { queryKeys } from "@/constants/queryKeys";
import { PostType } from "@/types/api/community.types";
import { notFound } from "next/navigation";
import { CommunityContent } from "../_components/CommunityContent";

const ALLOWED_POST_TYPES: PostType[] = [
  "discussion",
  "achievement",
  "partner_search",
  "tip",
  "competition",
];

interface CommunityTypePageProps {
  params: Promise<{ local: string; postType: PostType }>;
}

export default async function CommunityTypePage({
  params,
}: CommunityTypePageProps) {
  const { postType } = await params;

  // 1. Validation: Ensure we are on a valid community page type.
  if (!ALLOWED_POST_TYPES.includes(postType)) {
    notFound();
  }

  const queryClient = getQueryClient();

  // 2. Dynamic Filters: This object is now correctly built using the `postType` from the URL.
  // This is the source of truth for this page's data.
  const filters = { post_type: postType, ordering: "-created_at" };

  // 3. Pre-fetching: We use the dynamic `filters` to pre-fetch the correct data on the server.
  await queryClient.prefetchInfiniteQuery({
    queryKey: queryKeys.community.posts.list(filters),
    queryFn: getCommunityPosts,
    initialPageParam: 1,
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {/* 4. Prop Drilling: We pass the dynamic `postType` and `filters` down to the client component. */}
      <CommunityContent postType={postType} filters={filters} />
    </HydrationBoundary>
  );
}
