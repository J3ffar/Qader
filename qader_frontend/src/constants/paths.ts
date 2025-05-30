export const PATHS = {
  HOME: "/",
  ABOUT: "/about",
  PARTNERS: "/partners",
  STUDY_PREVIEW: "/study-preview",
  FAQ: "/questions",
  CONTACT: "/contact",
  TERMS_AND_CONDITIONS: "/conditions",
  LOGIN: "/login",
  SIGNUP: "/signup",
  COMPLETE_PROFILE: "/complete-profile",
  FORGOT_PASSWORD: "/forgot-password",
  STUDY: {
    HOME: "/study", // Main study dashboard
    DETERMINE_LEVEL: {
      LIST: "/study/determine-level",
      START: "/study/determine-level/start",
      ATTEMPT: (attemptId: number | string) =>
        `/study/determine-level/attempt/${attemptId}`,
      REVIEW: (attemptId: number | string) =>
        `/study/determine-level/attempt/${attemptId}/review`,
      SCORE: (attemptId: number | string) =>
        `/study/determine-level/attempt/${attemptId}/score`,
    },
    // ... other study sections
  },
  SETTINGS: "/settings",
  ADMIN_DASHBOARD: "/admin/dashboard",
  // ... other paths
};
