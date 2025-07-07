import { apiClient } from "@/services/apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import type {
  Page,
  UpdatePagePayload,
  ContentImage,
  UploadImagePayload,
  PageListItem,
  HomepageFeatureCard,
  HomepageStatistic,
} from "@/types/api/admin/content.types";
import { PaginatedResponse } from "@/types/api";

// --- Pages ---

export const getPages = async (
  params: { ordering?: string } = {}
): Promise<PaginatedResponse<Page>> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.PAGES, { params });
};

export const getPageBySlug = async (slug: string): Promise<Page> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.PAGE_DETAIL(slug));
};

export const updatePage = async ({
  slug,
  payload,
}: {
  slug: string;
  payload: UpdatePagePayload;
}): Promise<Page> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.PAGE_DETAIL(slug), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
};

// --- Content Images ---

export const uploadPageImage = async ({
  pageSlug,
  payload,
}: {
  pageSlug: string;
  payload: UploadImagePayload;
}): Promise<ContentImage> => {
  const formData = new FormData();
  formData.append("image", payload.image);
  formData.append("name", payload.name);
  formData.append("alt_text", payload.alt_text);
  if (payload.slug) {
    formData.append("slug", payload.slug);
  }

  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.PAGE_IMAGES(pageSlug), {
    method: "POST",
    body: formData,
  });
};

// Other service functions (deleteImage, getFaqs, etc.) would go here

// --- Homepage Feature Cards ---

export const getHomepageFeatures = async (): Promise<PaginatedResponse<HomepageFeatureCard>> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.HOMEPAGE_FEATURES);
};

export const createHomepageFeature = async (payload: Omit<HomepageFeatureCard, 'id'>): Promise<HomepageFeatureCard> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.HOMEPAGE_FEATURES, {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const updateHomepageFeature = async ({ id, payload }: { id: number; payload: Partial<Omit<HomepageFeatureCard, 'id'>> }): Promise<HomepageFeatureCard> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.HOMEPAGE_FEATURE_DETAIL(id), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
};

export const deleteHomepageFeature = async (id: number): Promise<void> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.HOMEPAGE_FEATURE_DETAIL(id), {
    method: "DELETE",
  });
};

// Placeholder for Homepage Statistics services - to be implemented next
export const getHomepageStats = async (): Promise<PaginatedResponse<HomepageStatistic>> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.HOMEPAGE_STATS);
};
