import { PaginatedResponse } from ".";

export interface LearningSubSectionBrief {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  order: number;
  is_active: boolean;
  // Add any other fields if present in the brief subsection object
}

export interface LearningSection {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  order: number;
  subsections: LearningSubSectionBrief[]; // Array of brief subsection details
}

export type PaginatedLearningSections = PaginatedResponse<LearningSection>; // Assuming PaginatedResponse is defined elsewhere

// Helper interface for form state
export interface SectionSelectionState {
  isSelected: boolean; // Is the main section itself selected (meaning all its subsections)
  selectedSubsections: Record<string, boolean>; // { [subsectionSlug]: true/false }
}
