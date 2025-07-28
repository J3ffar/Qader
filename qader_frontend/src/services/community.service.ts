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
import { User } from "@/types/api/user.types";
import { CommunityPostDetail } from "@/types/api/community.types";
import { apiClient } from "./apiClient";
import { PartnerRequest } from "@/types/api/community.types";

export const getCommunityPosts = async ({ pageParam = 1, queryKey }: any) => {
  const [, , , filters] = queryKey;
  return await apiClient<PaginatedResponse<CommunityPostList>>(
    API_ENDPOINTS.COMMUNITY.POSTS,
    {
      params: { ...filters, page: pageParam },
    }
  );
};

export const getPostDetails = async (postId: number) => {
  return await apiClient<CommunityPostDetail>(
    API_ENDPOINTS.COMMUNITY.POST_DETAIL(postId)
  );
};

export const createPost = async (payload: CreatePostPayload) => {
  const formData = new FormData();
  formData.append("post_type", payload.post_type);
  formData.append("content", payload.content);
  if (payload.title) formData.append("title", payload.title);
  if (payload.image) formData.append("image", payload.image);
  if (payload.section_filter) {
    formData.append("section_filter", payload.section_filter.toString());
  }
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

// This function now uses the more specific query key
export const getRepliesForPost = async ({ pageParam = 1, queryKey }: any) => {
  const [, , postId, filters] = queryKey; // Deconstruct to get postId
  return await apiClient<PaginatedResponse<CommunityReply>>(
    API_ENDPOINTS.COMMUNITY.REPLIES(postId),
    {
      params: { ...filters, page: pageParam },
    }
  );
};

// Renamed and enhanced to support threaded replies
export const createReply = async ({
  postId,
  content,
  parentReplyId,
}: {
  postId: number;
  content: string;
  parentReplyId?: number;
}) => {
  return await apiClient<CommunityReply>(
    API_ENDPOINTS.COMMUNITY.REPLIES(postId),
    {
      method: "POST",
      body: JSON.stringify({ content, parent_reply_id: parentReplyId }),
    }
  );
};

// NEW: Service function to like a reply
export const toggleReplyLike = async (replyId: number) => {
  return await apiClient<ToggleLikeResponse>(
    API_ENDPOINTS.COMMUNITY.REPLY_TOGGLE_LIKE(replyId),
    {
      method: "POST",
    }
  );
};

export const searchPartners = async ({ pageParam = 1, queryKey }: any) => {
  const [, , , filters] = queryKey;
  return await apiClient<PaginatedResponse<User>>(
    API_ENDPOINTS.COMMUNITY.PARTNERS,
    {
      params: { ...filters, page: pageParam },
    }
  );
};

export const sendPartnerRequest = async (toUserId: number) => {
  return await apiClient<PartnerRequest>(
    API_ENDPOINTS.COMMUNITY.PARTNER_REQUESTS,
    {
      method: "POST",
      body: JSON.stringify({ to_user_id: toUserId }),
    }
  );
};

export const getPartnerRequests = async ({ queryKey }: any) => {
  const [, , , filters] = queryKey; // e.g., { direction: 'sent' }
  return await apiClient<PaginatedResponse<PartnerRequest>>(
    API_ENDPOINTS.COMMUNITY.PARTNER_REQUESTS,
    {
      params: filters,
    }
  );
};

export const acceptPartnerRequest = async (requestId: number) => {
  return await apiClient<PartnerRequest>(
    API_ENDPOINTS.COMMUNITY.PARTNER_REQUEST_ACCEPT(requestId),
    {
      method: "POST",
    }
  );
};

export const rejectPartnerRequest = async (requestId: number) => {
  return await apiClient<PartnerRequest>(
    API_ENDPOINTS.COMMUNITY.PARTNER_REQUEST_REJECT(requestId),
    {
      method: "POST",
    }
  );
};
