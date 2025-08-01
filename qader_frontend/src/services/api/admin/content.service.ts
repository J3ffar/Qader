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
  PartnerCategory,
  PartnerCategoryPayload,
  FaqCategory,
  FaqItem,
  ContactMessage,
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

export const getHomepageFeatures = async (): Promise<
  PaginatedResponse<HomepageFeatureCard>
> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.HOMEPAGE_FEATURES);
};

export const createHomepageFeature = async (
  payload: Omit<HomepageFeatureCard, "id">
): Promise<HomepageFeatureCard> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.HOMEPAGE_FEATURES, {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const updateHomepageFeature = async ({
  id,
  payload,
}: {
  id: number;
  payload: Partial<Omit<HomepageFeatureCard, "id">>;
}): Promise<HomepageFeatureCard> => {
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

// --- Homepage Statistic ---

export const getHomepageStats = async (): Promise<
  PaginatedResponse<HomepageStatistic>
> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.HOMEPAGE_STATS);
};

export const createHomepageStat = async (
  payload: Omit<HomepageStatistic, "id">
): Promise<HomepageStatistic> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.HOMEPAGE_STATS, {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const updateHomepageStat = async ({
  id,
  payload,
}: {
  id: number;
  payload: Partial<Omit<HomepageStatistic, "id">>;
}): Promise<HomepageStatistic> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.HOMEPAGE_STAT_DETAIL(id), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
};

export const deleteHomepageStat = async (id: number): Promise<void> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.HOMEPAGE_STAT_DETAIL(id), {
    method: "DELETE",
  });
};

// --- Partner Categories ---

const buildPartnerFormData = (
  payload: Partial<PartnerCategoryPayload>
): FormData => {
  const formData = new FormData();
  Object.entries(payload).forEach(([key, value]) => {
    if (key === "icon_image" && value instanceof File) {
      formData.append(key, value);
    } else if (
      value !== null &&
      value !== undefined &&
      typeof value !== "object"
    ) {
      formData.append(key, String(value));
    }
  });
  return formData;
};

export const getPartnerCategories = async (): Promise<
  PaginatedResponse<PartnerCategory>
> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.PARTNER_CATEGORIES);
};

export const createPartnerCategory = async (
  payload: PartnerCategoryPayload
): Promise<PartnerCategory> => {
  const formData = buildPartnerFormData(payload);
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.PARTNER_CATEGORIES, {
    method: "POST",
    body: formData,
  });
};

export const updatePartnerCategory = async ({
  id,
  payload,
}: {
  id: number;
  payload: Partial<PartnerCategoryPayload>;
}): Promise<PartnerCategory> => {
  const formData = buildPartnerFormData(payload);
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.PARTNER_CATEGORY_DETAIL(id), {
    method: "PATCH",
    body: formData,
  });
};

export const deletePartnerCategory = async (id: number): Promise<void> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.PARTNER_CATEGORY_DETAIL(id), {
    method: "DELETE",
  });
};

// --- FAQ Categories ---

export const getFaqCategories = async (): Promise<
  PaginatedResponse<FaqCategory>
> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.FAQ_CATEGORIES);
};

export const createFaqCategory = async (
  payload: Omit<FaqCategory, "id">
): Promise<FaqCategory> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.FAQ_CATEGORIES, {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const updateFaqCategory = async ({
  id,
  payload,
}: {
  id: number;
  payload: Partial<Omit<FaqCategory, "id">>;
}): Promise<FaqCategory> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.FAQ_CATEGORY_DETAIL(id), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
};

export const deleteFaqCategory = async (id: number): Promise<void> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.FAQ_CATEGORY_DETAIL(id), {
    method: "DELETE",
  });
};

// --- FAQ Items ---

export const getFaqItems = async (
  categoryId: number
): Promise<PaginatedResponse<FaqItem>> => {
  // Assuming the API supports filtering items by category ID
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.FAQ_ITEMS, {
    params: { category: categoryId },
  });
};

export const createFaqItem = async (
  payload: Omit<FaqItem, "id">
): Promise<FaqItem> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.FAQ_ITEMS, {
    method: "POST",
    body: JSON.stringify(payload),
  });
};

export const updateFaqItem = async ({
  id,
  payload,
}: {
  id: number;
  payload: Partial<Omit<FaqItem, "id">>;
}): Promise<FaqItem> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.FAQ_ITEM_DETAIL(id), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
};

export const deleteFaqItem = async (id: number): Promise<void> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.FAQ_ITEM_DETAIL(id), {
    method: "DELETE",
  });
};

// --- Contact Messages ---

export type GetContactMessagesParams = {
  page?: number;
  status?: string;
  email?: string;
  search?: string;
  ordering?: string;
};

export const getContactMessages = async (
  params: GetContactMessagesParams
): Promise<PaginatedResponse<ContactMessage>> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.CONTACT_MESSAGES, { params });
};

export const updateContactMessage = async ({
  id,
  payload,
}: {
  id: number;
  payload: { status?: string; response?: string };
}): Promise<ContactMessage> => {
  return apiClient(API_ENDPOINTS.ADMIN.CONTENT.CONTACT_MESSAGE_DETAIL(id), {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
};
