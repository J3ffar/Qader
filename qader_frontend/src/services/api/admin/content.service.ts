import { apiClient } from "@/services/apiClient";
import { API_ENDPOINTS } from "@/constants/api";
import type {
  Page,
  UpdatePagePayload,
  ContentImage,
  UploadImagePayload,
  PageListItem,
} from "@/types/api/admin/content.types";
import { PaginatedResponse } from "@/types/api";

// --- Pages ---

export const getPages = async (): Promise<PaginatedResponse<PageListItem>> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.PAGES);
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
