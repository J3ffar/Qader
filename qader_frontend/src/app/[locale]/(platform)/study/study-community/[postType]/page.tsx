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
  params: { postType: PostType };
}

export default async function CommunityTypePage({
  params,
}: CommunityTypePageProps) {
  const { postType } = params;

  if (!ALLOWED_POST_TYPES.includes(postType)) {
    notFound();
  }

  const queryClient = getQueryClient();

  // Pre-fetch data for the *default* sort order of this page.
  // The client will handle fetching data for other sort orders.
  const defaultFilters = { post_type: postType, ordering: "-created_at" };

  await queryClient.prefetchInfiniteQuery({
    queryKey: queryKeys.community.posts.list(defaultFilters),
    queryFn: getCommunityPosts,
    initialPageParam: 1,
  });

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      {/* The client component now only needs the postType */}
      <CommunityContent postType={postType} />
    </HydrationBoundary>
  );
}
