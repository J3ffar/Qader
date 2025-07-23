import { PaginatedResponse } from "..";

// Base types for relational data
export interface AdminLearningBase {
  id: number;
  name: string;
  slug: string;
}

export interface AdminSection extends AdminLearningBase {
  description: string | null;
  order: number;
  created_at: string;
  updated_at: string;
}

export interface AdminSubSection extends AdminLearningBase {
  description: string | null;
  order: number;
  section_name: string;
  section_slug: string;
  created_at: string;
  updated_at: string;
}

export interface AdminSkill extends AdminLearningBase {
  description: string | null;
  subsection_name: string;
  subsection_slug: string;
  created_at: string;
  updated_at: string;
}

// Question related types
export interface AdminQuestionOptions {
  A: string;
  B: string;
  C: string;
  D: string;
}

export type CorrectAnswer = "A" | "B" | "C" | "D";

export interface AdminQuestionUsageByTestType {
  level_assessment: number;
  practice: number;
  simulation: number;
  traditional: number;
}

export interface AdminQuestion {
  id: number;
  question_text: string;
  image: string | null;
  options: AdminQuestionOptions;
  difficulty: number;
  is_active: boolean;
  section: AdminLearningBase;
  subsection: AdminLearningBase;
  skill: AdminLearningBase | null;
  total_usage_count: number;
  usage_by_test_type: AdminQuestionUsageByTestType | null;
  created_at: string;
  updated_at: string;
  explanation?: string | null;
  hint?: string | null;
  solution_method_summary?: string | null;
  correct_answer?: CorrectAnswer;
}

// API Response types
export type AdminSectionsListResponse = PaginatedResponse<AdminSection>;
export type AdminSubSectionsListResponse = PaginatedResponse<AdminSubSection>;
export type AdminSkillsListResponse = PaginatedResponse<AdminSkill>;
export type AdminQuestionsListResponse = PaginatedResponse<AdminQuestion>;

// Form / Request Body types
export interface AdminSectionCreateUpdate {
  name: string;
  slug?: string;
  description?: string;
  order?: number;
}

export interface AdminSubSectionCreateUpdate {
  name: string;
  slug?: string;
  description?: string;
  order?: number;
  section_id: number;
}

export interface AdminSkillCreateUpdate {
  name: string;
  slug?: string;
  description?: string;
  subsection_id: number;
}

export interface AdminQuestionCreateUpdate {
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: CorrectAnswer;
  difficulty: number;
  subsection_id: number;
  is_active?: boolean;
  skill_id?: number | null;
  image?: File | null;
  explanation?: string | null;
  hint?: string | null;
  solution_method_summary?: string | null;
}
