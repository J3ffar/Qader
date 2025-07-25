import { API_ENDPOINTS } from "@/constants/api";
import { apiClient } from "@/services/apiClient";
import type {
  AdminSection,
  AdminSectionsListResponse,
  AdminSubSection,
  AdminSubSectionsListResponse,
  AdminSkill,
  AdminSkillsListResponse,
  AdminQuestion,
  AdminQuestionsListResponse,
  AdminSectionCreateUpdate,
  AdminSubSectionCreateUpdate,
  AdminSkillCreateUpdate,
  AdminQuestionCreateUpdate,
} from "@/types/api/admin/learning.types";

// This converts a standard object to FormData
export const objectToFormData = (obj: Record<string, any>): FormData => {
  const formData = new FormData();
  for (const key in obj) {
    if (obj[key] !== null && obj[key] !== undefined) {
      formData.append(key, obj[key]);
    }
  }
  return formData;
};
// --- Sections ---
export const getAdminSections = (params: Record<string, any> = {}) =>
  apiClient<AdminSectionsListResponse>(API_ENDPOINTS.ADMIN.LEARNING.SECTIONS, {
    params,
  });

export const createAdminSection = (data: AdminSectionCreateUpdate) =>
  apiClient<AdminSection>(API_ENDPOINTS.ADMIN.LEARNING.SECTIONS, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateAdminSection = (
  id: number,
  data: Partial<AdminSectionCreateUpdate>
) =>
  apiClient<AdminSection>(API_ENDPOINTS.ADMIN.LEARNING.SECTION_DETAIL(id), {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deleteAdminSection = (id: number) =>
  apiClient(API_ENDPOINTS.ADMIN.LEARNING.SECTION_DETAIL(id), {
    method: "DELETE",
  });

// --- Sub-Sections ---
export const getAdminSubSections = (params: Record<string, any> = {}) =>
  apiClient<AdminSubSectionsListResponse>(
    API_ENDPOINTS.ADMIN.LEARNING.SUBSECTIONS,
    { params }
  );

export const createAdminSubSection = (data: AdminSubSectionCreateUpdate) =>
  apiClient<AdminSubSection>(API_ENDPOINTS.ADMIN.LEARNING.SUBSECTIONS, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateAdminSubSection = (
  id: number,
  data: Partial<AdminSubSectionCreateUpdate>
) =>
  apiClient<AdminSubSection>(
    API_ENDPOINTS.ADMIN.LEARNING.SUBSECTION_DETAIL(id),
    { method: "PATCH", body: JSON.stringify(data) }
  );

export const deleteAdminSubSection = (id: number) =>
  apiClient(API_ENDPOINTS.ADMIN.LEARNING.SUBSECTION_DETAIL(id), {
    method: "DELETE",
  });

// --- Skills ---
export const getAdminSkills = (params: Record<string, any> = {}) =>
  apiClient<AdminSkillsListResponse>(API_ENDPOINTS.ADMIN.LEARNING.SKILLS, {
    params,
  });

export const createAdminSkill = (data: AdminSkillCreateUpdate) =>
  apiClient<AdminSkill>(API_ENDPOINTS.ADMIN.LEARNING.SKILLS, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateAdminSkill = (
  id: number,
  data: Partial<AdminSkillCreateUpdate>
) =>
  apiClient<AdminSkill>(API_ENDPOINTS.ADMIN.LEARNING.SKILL_DETAIL(id), {
    method: "PATCH",
    body: JSON.stringify(data),
  });

export const deleteAdminSkill = (id: number) =>
  apiClient(API_ENDPOINTS.ADMIN.LEARNING.SKILL_DETAIL(id), {
    method: "DELETE",
  });

// --- Questions ---
export const getAdminQuestions = (params: Record<string, any> = {}) =>
  apiClient<AdminQuestionsListResponse>(
    API_ENDPOINTS.ADMIN.LEARNING.QUESTIONS,
    { params }
  );

export const getAdminQuestionDetail = (id: number) =>
  apiClient<AdminQuestion>(API_ENDPOINTS.ADMIN.LEARNING.QUESTION_DETAIL(id));

export const createAdminQuestion = (data: AdminQuestionCreateUpdate) => {
  const formData = objectToFormData(data);
  return apiClient<AdminQuestion>(API_ENDPOINTS.ADMIN.LEARNING.QUESTIONS, {
    method: "POST",
    body: formData,
  });
};

export const updateAdminQuestion = (
  id: number,
  data: Partial<AdminQuestionCreateUpdate> & { image?: null }
) => {
  const isMultipart = data instanceof FormData;

  const headers = isMultipart
    ? {} // Let the browser set the Content-Type for FormData
    : { "Content-Type": "application/json" };

  const body = isMultipart ? data : JSON.stringify(data);

  return apiClient<AdminQuestion>(
    API_ENDPOINTS.ADMIN.LEARNING.QUESTION_DETAIL(id),
    {
      method: "PATCH",
      body,
    }
  );
};

export const deleteAdminQuestion = (id: number) =>
  apiClient(API_ENDPOINTS.ADMIN.LEARNING.QUESTION_DETAIL(id), {
    method: "DELETE",
  });

// --- Fetch all for Selects ---

// Assuming the API supports a `page_size` param to fetch more items at once.
const ALL_ITEMS_PARAMS = { page_size: 1000 };

export const getAdminAllSections = () =>
  apiClient<AdminSectionsListResponse>(API_ENDPOINTS.ADMIN.LEARNING.SECTIONS, {
    params: ALL_ITEMS_PARAMS,
  });

export const getAdminAllSubSections = (sectionId?: number) => {
  const params = sectionId
    ? { ...ALL_ITEMS_PARAMS, section__id: sectionId }
    : ALL_ITEMS_PARAMS;
  return apiClient<AdminSubSectionsListResponse>(
    API_ENDPOINTS.ADMIN.LEARNING.SUBSECTIONS,
    { params }
  );
};

export const getAdminAllSkills = (subsectionId?: number) => {
  const params = subsectionId
    ? { ...ALL_ITEMS_PARAMS, subsection__id: subsectionId }
    : ALL_ITEMS_PARAMS;
  return apiClient<AdminSkillsListResponse>(
    API_ENDPOINTS.ADMIN.LEARNING.SKILLS,
    { params }
  );
};
