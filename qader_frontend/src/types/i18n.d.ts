// Import types from common namespaces
import type enAuthMessages from "@/locales/en/auth.json";
import type enCommonMessages from "@/locales/en/common.json";
import type enNavMessages from "@/locales/en/nav.json";

// Import types for each file within the 'study' namespace
import type enStudyPage from "@/locales/en/study/StudyPage.json";
import type enDetermineLevel from "@/locales/en/study/determineLevel.json";
import type enTests from "@/locales/en/study/tests.json";
import type enTraditionalLearning from "@/locales/en/study/traditionalLearning.json";
import type enStatistics from "@/locales/en/study/statistics.json";
import type enConversationalLearning from "@/locales/en/study/conversationalLearning.json";
import type enEmergencyMode from "@/locales/en/study/emergencyMode.json";
import type enReview from "@/locales/en/study/review.json";
import type enSettings from "@/locales/en/study/settings.json";

// We use an intersection type (&) to merge the types of all our study files
// into a single, comprehensive 'StudyMessages' type.
type StudyMessages = typeof enStudyPage &
  typeof enDetermineLevel &
  typeof enTests &
  typeof enTraditionalLearning &
  typeof enStatistics &
  typeof enConversationalLearning &
  typeof enEmergencyMode &
  typeof enReview &
  typeof enSettings;

/**
 * Represents the complete structure of messages used by next-intl.
 * This structure should mirror the `messages` object returned in `src/config/i18n.config.ts`.
 */
export type AppMessages = {
  Auth: typeof enAuthMessages;
  Common: typeof enCommonMessages;
  Nav: typeof enNavMessages;
  Study: StudyMessages; // Use the merged type here
};

// This tells TypeScript that the `IntlMessages` type used by next-intl
// in your project corresponds to our fully structured `AppMessages`.
declare global {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface IntlMessages extends AppMessages {}
}
