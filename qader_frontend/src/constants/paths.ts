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
      // Root for determine level section, could list available tests or info
      LIST: "/study/determine-level",
      START: "/study/determine-level/start",
      // Taking a specific test attempt
      ATTEMPT: (attemptId: number | string) =>
        `/study/determine-level/attempt/${attemptId}`,
      // Reviewing answers for a completed attempt
      REVIEW: (attemptId: number | string) =>
        `/study/determine-level/attempt/${attemptId}/review`,
      // Viewing the score/results of an attempt
      SCORE: (attemptId: number | string) =>
        `/study/determine-level/attempt/${attemptId}/score`,
    },

    TRADITIONAL_LEARNING: {
      HOME: "/study/traditional-learning", // Main page for this learning mode
    },

    CONVERSATIONAL_LEARNING: {
      HOME: "/study/conversation-learning", // Main page for this learning mode
    },

    SIMULATION_TESTS: {
      HOME: "/study/simulation-tests", // List of available simulation tests
    },

    REWARDS_AND_COMPETITIONS: "/study/rewards-and-competitions",
    STATISTICS: "/study/statistics",
    CHALLENGE_COLLEAGUES: "/study/challenge-peers",
    STUDY_COMMUNITY: "/study/study-community", // Could be a forum, groups, etc.
    BLOG: {
      HOME: "/study/blog",
    },
    ADMIN_SUPPORT: "/study/admin-support", // Ticketing, FAQ, contact for support
    EMERGENCY_MODE: "/study/emergency-mode", // Special mode, perhaps for quick reviews or offline access

    // Consider adding other common study sections here as they are developed
  },

  SETTINGS: {
    PROFILE: "/settings/profile",
    ACCOUNT: "/settings/account",
    SUBSCRIPTION: "/settings/subscription",
    NOTIFICATIONS: "/settings/notifications",
    // Main settings page can be one of the above or its own
    HOME: "/settings", // Or simply "/settings" and redirect to a default tab
  },
  ADMIN_DASHBOARD: "/admin/dashboard",
  // ... other paths
};
