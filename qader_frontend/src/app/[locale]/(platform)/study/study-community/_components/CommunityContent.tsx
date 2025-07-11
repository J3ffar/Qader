"use client";

import { PostType } from "@/types/api/community.types";
import { CommunityFeed } from "./CommunityFeed";
import { CreatePostDialog } from "./CreatePostDialog";
import { Button } from "@/components/ui/button";
import { Filter } from "lucide-react";

interface CommunityContentProps {
  postType: PostType;
  // This prop now holds the dynamic filters from the server component.
  filters: { post_type: string; ordering: string };
}

const CAN_CREATE_POST_TYPES: PostType[] = ["discussion", "achievement", "tip"];

export function CommunityContent({ postType, filters }: CommunityContentProps) {
  const canCreatePost = CAN_CREATE_POST_TYPES.includes(postType);

  const renderContent = () => {
    switch (postType) {
      case "discussion":
      case "achievement":
      case "tip":
      case "competition":
        // Crucially, pass the dynamic `filters` prop to the feed.
        return <CommunityFeed filters={filters} />;

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
      <div className="flex justify-between items-center mb-4">
        {canCreatePost ? <CreatePostDialog postType={postType} /> : <div />}{" "}
        {/* Placeholder to maintain layout */}
        <Button variant="outline">
          <Filter className="ms-2 h-4 w-4" />
          تصفية
        </Button>
      </div>
      {renderContent()}
    </div>
  );
}
