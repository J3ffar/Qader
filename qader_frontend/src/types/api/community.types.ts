import { PaginatedResponse } from ".";
import { SimpleUser } from "./user.types";

export type PostType =
  | "achievement"
  | "competition"
  | "discussion"
  | "partner_search"
  | "tip";

export interface CommunityPostList {
  id: number;
  author: SimpleUser;
  post_type: PostType;
  title: string | null;
  image_url: string | null;
  section_filter: {
    id: number;
    name: string;
    slug: string;
  } | null;
  content_excerpt: string;
  reply_count: number;
  like_count: number;
  is_liked_by_user: boolean;
  created_at: string; // ISO 8601 datetime string
  tags: string[];
  is_pinned: boolean;
  is_closed: boolean;
}

export interface CommunityReply {
  id: number;
  author: SimpleUser;
  content: string;
  like_count: number;
  is_liked_by_user: boolean;
  created_at: string;
  updated_at: string;
  post: number;
  parent_reply_read_id: number | null;
  child_replies_count: number;
}

export interface CommunityPostDetail
  extends Omit<CommunityPostList, "content_excerpt"> {
  content: string;
  updated_at: string;
  replies: PaginatedResponse<CommunityReply>;
}

export interface CreatePostPayload {
  post_type: PostType;
  content: string;
  title?: string;
  image?: File;
  section_filter?: string;
  tags?: string[];
}

export interface CreateReplyPayload {
  content: string;
  parent_reply_id?: number;
}

export interface ToggleLikeResponse {
  status: string;
  liked: boolean;
  like_count: number;
}
