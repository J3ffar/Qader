export interface BlogAuthor {
  id: number;
  username: string;
  full_name: string;
  preferred_name: string;
  profile_picture_url: string | null;
  bio: string;
  linkedin_url: string | null;
  twitter_url: string | null;
  facebook_url: string | null;
  instagram_url: string | null;
}
export interface BlogPost {
  id: number;
  title: string;
  slug: string;
  author: BlogAuthor;
  published_at: string;
  excerpt: string;
  tags: string[];
  content: string;
  image: string | null;
}

export interface PaginatedBlogPostResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: BlogPost[];
}
export interface AdviceRequestInput {
  problem_type: string;
  description: string;
}
export interface GetBlogPostsParams {
  page?: number;
  page_size?: number;
  search?: string;
  ordering?: string;
  tag?: string;
}
export interface AdviceRequestResponse {
  id: number;
  problem_type: string;
  description: string;
  status: "submitted";
  created_at: string;
}
