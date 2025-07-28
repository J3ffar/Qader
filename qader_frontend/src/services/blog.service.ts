import { API_ENDPOINTS } from "@/constants/api";
import type {
  BlogPost,
  GetBlogPostsParams,
  PaginatedBlogPostResponse,
} from "@/types/api/blog.types";
import {
  AdviceRequestInput,
  AdviceRequestResponse,
} from "@/types/api/blog.types";
import { apiClient } from "./apiClient";

export const submitAdviceRequest = async (
  input: AdviceRequestInput
): Promise<AdviceRequestResponse> => {
  return apiClient<AdviceRequestResponse>(API_ENDPOINTS.Blog.adviceRequests, {
    method: "POST",
    body: JSON.stringify(input),
  });
};

export const getBlogPosts = async (
  params?: GetBlogPostsParams
): Promise<PaginatedBlogPostResponse> => {
  return apiClient<PaginatedBlogPostResponse>(API_ENDPOINTS.Blog.POSTS, {
    method: "GET",
    params,
  });
};

export const getBlogPostBySlug = async (slug: string): Promise<BlogPost> => {
  const url = `${API_ENDPOINTS.Blog.POSTS}/${slug}/`.replace(/\/{2,}/g, "/");

  return apiClient<BlogPost>(url, { method: "GET" });
};
