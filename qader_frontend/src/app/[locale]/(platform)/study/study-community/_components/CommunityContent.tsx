"use client";

import { useState } from "react";
import { PostType } from "@/types/api/community.types";
import { CommunityFeed } from "./CommunityFeed";
import { CreatePostDialog } from "./CreatePostDialog";
import { CommunitySortMenu } from "./CommunitySortMenu";

type SortOption =
  | "-created_at"
  | "created_at"
  | "-like_count"
  | "-is_pinned"
  | "is_closed";

interface CommunityContentProps {
  postType: PostType;
}

const CAN_CREATE_POST_TYPES: PostType[] = ["discussion", "achievement", "tip"];

export function CommunityContent({ postType }: CommunityContentProps) {
  const [sortOrder, setSortOrder] = useState<SortOption>("-is_pinned");
  const canCreatePost = CAN_CREATE_POST_TYPES.includes(postType);

  // Combine postType and sortOrder to create the dynamic filters object
  const filters = {
    post_type: postType,
    ordering: sortOrder,
  };

  const renderContent = () => {
    switch (postType) {
      case "discussion":
      case "achievement":
      case "tip":
      case "competition":
        // Pass the dynamic filters object to the feed.
        // The `key` is crucial to force a full remount and state reset of the feed when filters change.
        return (
          <CommunityFeed key={`${postType}-${sortOrder}`} filters={filters} />
        );

      case "partner_search":
        return (
          <div className="flex items-center justify-center h-96 rounded-lg border-2 border-dashed">
            <p className="text-muted-foreground">
              UI for 'Partner Search' will be implemented here.
            </p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4 flex-wrap gap-2">
        {canCreatePost ? <CreatePostDialog postType={postType} /> : <div />}
        <CommunitySortMenu
          currentSort={sortOrder}
          onSortChange={(newSort) => setSortOrder(newSort)}
        />
      </div>
      {renderContent()}
    </div>
  );
}
