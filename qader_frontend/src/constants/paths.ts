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
    HOME: "/study", // Main study dashboard/landing page for logged-in users

    DETERMINE_LEVEL: {
      LIST: "/study/determine-level",
      START: "/study/determine-level/start",
      ATTEMPT: (attemptId: number | string) =>
        `/study/determine-level/attempt/${attemptId}`,
      REVIEW: (attemptId: number | string) =>
        `/study/determine-level/attempt/${attemptId}/review`,
      SCORE: (attemptId: number | string) =>
        `/study/determine-level/attempt/${attemptId}/score`,
      // ADD THIS NEW PATH
      DETAILS: (attemptId: number | string) =>
        `/study/determine-level/attempt/${attemptId}/details`,
    },

    TRADITIONAL_LEARNING: {
      LIST: "/study/traditional-learning", // Main page for this learning mode
      SESSION: (attemptId: number | string) =>
        `/study/traditional-learning/session/${attemptId}`,
      SCORE: (attemptId: number | string) =>
        `/study/traditional-learning/session/${attemptId}/score`,
      REVIEW: (attemptId: number | string) =>
        `/study/traditional-learning/session/${attemptId}/review`,
    },

    CONVERSATIONAL_LEARNING: {
      HOME: "/study/conversation-learning", // Main page for this learning mode
    },

    TESTS: {
      LIST: "/study/tests",
      START: "/study/tests/start",
      ATTEMPT: (attemptId: number | string) =>
        `/study/tests/attempt/${attemptId}`,
      SCORE: (attemptId: number | string) =>
        `/study/tests/attempt/${attemptId}/score`,
      REVIEW: (attemptId: number | string, incorrectOnly = false) =>
        `/study/tests/attempt/${attemptId}/review${
          incorrectOnly ? "?incorrect_only=true" : ""
        }`,
    },

    REWARDS_AND_COMPETITIONS: "/study/rewards-and-competitions",
    STATISTICS: "/study/statistics",
    CHALLENGE_COLLEAGUES: "/study/challenge-peers",
    STUDY_COMMUNITY: "/study/study-community", // Could be a forum, groups, etc.
    COMMUNITY_DISCUSSION: "/study/study-community/discussion",
    COMMUNITY_ACHIEVEMENT: "/study/study-community/achievement",
    COMMUNITY_PARTNER_SEARCH: "/study/study-community/partner_search",
    COMMUNITY_TIPS: "/study/study-community/tip",
    COMMUNITY_COMPETITIONS: "/study/study-community/competition",
    BLOG: {
      HOME: "/study/blog",
    },
    ADMIN_SUPPORT: "/study/admin-support", // Ticketing, FAQ, contact for support
    EMERGENCY_MODE: "/study/emergency-mode", // Special mode, perhaps for quick reviews or offline access

    SETTINGS: {
      HOME: "/study/settings",
      PROFILE: "/study/settings/profile",
      ACCOUNT: "/study/settings/account",
      SUBSCRIPTION: "/study/settings/subscription",
      NOTIFICATIONS: "/study/settings/notifications",
    },
    // Consider adding other common study sections here as they are developed
  },

  ADMIN: {
    DASHBOARD: "/admin/dashboard",
    EMPLOYEES_MANAGEMENT: "/admin/employees",
    STUDENTS_MANAGEMENT: "/admin/students",
    STATISTICS_OVERVIEW: "/admin/statistics/overview",

    CONTENT_PAGES_LIST: "/admin/content/pages",
    CONTENT_PAGE_EDIT: (slug: string) => `/admin/content/pages/${slug}`,
    CONTENT_FAQS: "/admin/content/faqs",
    CONTENT_HOMEPAGE: "/admin/content/homepage",
    CONTENT_PARTNERS: "/admin/content/partners",
    CONTENT_CONTACT_MESSAGES: "/admin/content/contact",

    SUPPORT_TICKETS: "/admin/support",
    ANALYTICS: "/admin/analytics",
    SETTINGS: "/admin/settings",
    PROFILE: "/admin/profile",
  },
};
