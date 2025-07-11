import { API_ENDPOINTS } from "@/constants/api";
import { queryKeys } from "@/constants/queryKeys";
import { PaginatedResponse } from "@/types/api";
import {
  CommunityPostList,
  CreatePostPayload,
  CreateReplyPayload,
  CommunityReply,
  ToggleLikeResponse,
} from "@/types/api/community.types";
import { apiClient } from "./apiClient";

export const getCommunityPosts = async ({ pageParam = 1, queryKey }: any) => {
  const [, , , filters] = queryKey;
  return await apiClient<PaginatedResponse<CommunityPostList>>(
    API_ENDPOINTS.COMMUNITY.POSTS,
    {
      params: { ...filters, page: pageParam },
    }
  );
};

export const createPost = async (payload: CreatePostPayload) => {
  const formData = new FormData();
  formData.append("post_type", payload.post_type);
  formData.append("content", payload.content);
  if (payload.title) formData.append("title", payload.title);
  if (payload.image) formData.append("image", payload.image);
  // Add other fields as needed

  return await apiClient<CommunityPostList>(API_ENDPOINTS.COMMUNITY.POSTS, {
    method: "POST",
    body: formData,
  });
};

export const togglePostLike = async (postId: number) => {
  return await apiClient<ToggleLikeResponse>(
    API_ENDPOINTS.COMMUNITY.POST_TOGGLE_LIKE(postId),
    {
      method: "POST",
    }
  );
};

export const createReply = async ({
  postId,
  payload,
}: {
  postId: number;
  payload: CreateReplyPayload;
}) => {
  return await apiClient<CommunityReply>(
    API_ENDPOINTS.COMMUNITY.REPLIES(postId),
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

// ... other service functions like toggleReplyLike, getTags etc.
