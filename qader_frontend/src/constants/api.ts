export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://qader.vip";
export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_BASE_URL || "wss://qader.vip/ws";
export const API_VERSION = "v1";

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: "/auth/login/",
    SIGNUP: "/auth/signup/",
    CONFIRM_EMAIL: (uidb64: string, token: string) =>
      `/auth/confirm-email/${uidb64}/${token}/`,
    LOGOUT: "/auth/logout/", // Used by direct fetch in auth.service
    REFRESH_TOKEN: "/auth/token/refresh/", // Used by direct fetch in auth.service
    REQUEST_OTP: "/auth/password/reset/request-otp/",
    VERIFY_OTP: "/auth/password/reset/verify-otp/",
    RESET_PASSWORD_CONFIRM_OTP: "/auth/password/reset/confirm-otp/",
  },
  USERS: {
    ME: "/users/me/", // For GET and PATCH user profile
    COMPLETE_PROFILE: "/users/me/complete-profile/", // Specific endpoint for initial profile completion
    CHANGE_PASSWORD: "/users/me/change-password/",
    APPLY_SERIAL_CODE: "/users/me/apply-serial-code/", // Moved from STUDY to USERS as it's user-related
    SUBSCRIPTION_PLANS: "/users/subscription-plans/",
    CANCEL_SUBSCRIPTION: "/users/me/subscription/cancel/",
    GRADES: "/users/grades/",
    SUPPORT: {
      // <-- ADD THIS NEW SECTION
      TICKETS: "/support/tickets/",
      DETAIL: (id: number | string) => `/support/tickets/${id}/`,
      REPLIES: (id: number | string) => `/support/tickets/${id}/replies/`,
    },
  },
  ADMIN: {
    USERS: {
      LIST: "/admin/users/",
      DETAIL: (userId: number | string) => `/admin/users/${userId}/`,
      ADJUST_POINTS: (userId: number) =>
        `/admin/users/${userId}/adjust-points/`,
      POINT_LOG: (userId: number) => `/admin/users/${userId}/point-log/`,
      RESET_PASSWORD: (userId: number) =>
        `/admin/users/${userId}/reset-password/`,
      STATISTICS: (userId: number) => `/admin/users/${userId}/statistics/`,
      TEST_HISTORY: (userId: number) => `/admin/users/${userId}/test-history/`,
    },
    STATISTICS: {
      // NEW SECTION
      OVERVIEW: "/admin/statistics/overview/",
      EXPORT: "/admin/statistics/export/",
    },
    PERMISSIONS: "/admin/permissions/",
    SUPPORT: {
      // NEW SECTION
      TICKETS: "/admin/support/tickets/",
      TICKET_DETAIL: (id: number | string) => `/admin/support/tickets/${id}/`,
      REPLIES: (id: number | string) => `/admin/support/tickets/${id}/replies/`,
    },
    CONTENT: {
      // NEW SECTION
      // Pages
      PAGES: "/admin/content/pages/",
      PAGE_DETAIL: (slug: string) => `/admin/content/pages/${slug}/`,
      // Page-specific Images
      PAGE_IMAGES: (pageSlug: string) =>
        `/admin/content/pages/${pageSlug}/images/`,
      PAGE_IMAGE_DETAIL: (pageSlug: string, imageId: number | string) =>
        `/admin/content/pages/${pageSlug}/images/${imageId}/`,
      // FAQs
      FAQ_CATEGORIES: "/admin/content/faq-categories/",
      FAQ_CATEGORY_DETAIL: (id: number | string) =>
        `/admin/content/faq-categories/${id}/`,
      FAQ_ITEMS: "/admin/content/faq-items/",
      FAQ_ITEM_DETAIL: (id: number | string) =>
        `/admin/content/faq-items/${id}/`,
      // Contact Messages
      CONTACT_MESSAGES: "/admin/content/contact-messages/",
      CONTACT_MESSAGE_DETAIL: (id: number | string) =>
        `/admin/content/contact-messages/${id}/`,
      // Homepage
      HOMEPAGE_FEATURES: "/admin/content/homepage-features/",
      HOMEPAGE_FEATURE_DETAIL: (id: number | string) =>
        `/admin/content/homepage-features/${id}/`,
      HOMEPAGE_STATS: "/admin/content/homepage-stats/",
      HOMEPAGE_STAT_DETAIL: (id: number | string) =>
        `/admin/content/homepage-stats/${id}/`,
      // Partners
      PARTNER_CATEGORIES: "/admin/content/partner-categories/",
      PARTNER_CATEGORY_DETAIL: (id: number | string) =>
        `/admin/content/partner-categories/${id}/`,
    },
  },
  STUDY: {
    STATISTICS: "/study/statistics/",
    CONVERSATIONS: {
      // Grouped conversational learning endpoints
      BASE: "/study/conversations/", // For starting a conversation session
      MESSAGES: (sessionId: number | string) =>
        `/study/conversations/${sessionId}/messages/`,
      ASK_QUESTION: (sessionId: number | string) =>
        `/study/conversations/${sessionId}/ask-question/`,
      CONFIRM_UNDERSTANDING: (sessionId: number | string) =>
        `/study/conversations/${sessionId}/confirm-understanding/`,
      SUBMIT_TEST_ANSWER: (sessionId: number | string) =>
        `/study/conversations/${sessionId}/submit-test-answer/`,
    },
    EMERGENCY_MODE: {
      START: "/study/emergency-mode/start/",
      SESSION: (sessionId: number | string) =>
        `/study/emergency-mode/sessions/${sessionId}/`,
      QUESTIONS: (sessionId: number | string) =>
        `/study/emergency-mode/sessions/${sessionId}/questions/`,
      ANSWER: (sessionId: number | string) =>
        `/study/emergency-mode/sessions/${sessionId}/answer/`,
    },
    ATTEMPTS: {
      LIST: "/study/attempts/",
      DETAIL: (attemptId: number | string) => `/study/attempts/${attemptId}/`,
      ANSWER: (attemptId: number | string) =>
        `/study/attempts/${attemptId}/answer/`,
      CANCEL: (attemptId: number | string) =>
        `/study/attempts/${attemptId}/cancel/`,
      COMPLETE: (attemptId: number | string) =>
        `/study/attempts/${attemptId}/complete/`,
      REVIEW: (attemptId: number | string) =>
        `/study/attempts/${attemptId}/review/`,
      RETAKE: (attemptId: number | string) =>
        `/study/attempts/${attemptId}/retake/`,
    },
    START: {
      LEVEL_ASSESSMENT: "/study/start/level-assessment/",
      TRADITIONAL: "/study/start/traditional/",
      PRACTICE_SIMULATION: "/study/start/practice-simulation/",
    },
    TRADITIONAL_PRACTICE_INTERACTIONS: {
      // Grouped for clarity
      HINT: (attemptId: number | string, questionId: number | string) =>
        `/study/start/traditional/attempts/${attemptId}/questions/${questionId}/hint/`,
      REVEAL_ANSWER: (
        attemptId: number | string,
        questionId: number | string
      ) =>
        `/study/start/traditional/attempts/${attemptId}/questions/${questionId}/reveal-answer/`,
      REVEAL_EXPLANATION: (
        attemptId: number | string,
        questionId: number | string
      ) =>
        `/study/start/traditional/attempts/${attemptId}/questions/${questionId}/reveal-explanation/`,
      ELIMINATE: (attemptId: number | string, questionId: number | string) =>
        `/study/start/traditional/attempts/${attemptId}/questions/${questionId}/eliminate/`,
    },
    CHALLENGES: {
      LIST_AND_CREATE: "/challenges/challenges/",
      DETAIL: (id: number | string) => `/challenges/challenges/${id}/`,
      ACCEPT: (id: number | string) => `/challenges/challenges/${id}/accept/`,
      DECLINE: (id: number | string) => `/challenges/challenges/${id}/decline/`,
      CANCEL: (id: number | string) => `/challenges/challenges/${id}/cancel/`,
      READY: (id: number | string) => `/challenges/challenges/${id}/ready/`,
      ANSWER: (id: number | string) => `/challenges/challenges/${id}/answer/`,
      RESULTS: (id: number | string) => `/challenges/challenges/${id}/results/`,
      REMATCH: (id: number | string) => `/challenges/challenges/${id}/rematch/`,
      TYPES: "/challenges/types/",
    },
  },
  LEARNING: {
    SECTIONS: {
      LIST: "/learning/sections/",
      DETAIL: (slug: string) => `/learning/sections/${slug}/`,
    },
  },
  NOTIFICATIONS: {
    LIST: "/notifications/",
    MARK_READ: "/notifications/mark-read/",
    MARK_ALL_READ: "/notifications/mark-all-read/",
    UNREAD_COUNT: "/notifications/unread-count/",
  },
  GAMIFICATION: {
    REWARD_STORE: "/gamification/reward-store/",
    DAILY_POINTS_SUMMARY: "/gamification/points-summary/",
    STUDY_DAYS: "/gamification/study-days/",
    // Adding placeholders for other gamification endpoints that might exist or be added soon
    BADGES_LIST: "/gamification/badges/",
    MY_BADGES: "/gamification/my-badges/",
    POINTS_LOG: "/gamification/point-log/",
    GAMIFICATION_SUMMARY: "/gamification/summary/",
    POINT_LOG_DETAIL: (id: number | string) => `/gamification/point-log/${id}/`,
    REWARD_STORE_DETAIL: (id: number | string) =>
      `/gamification/reward-store/${id}/`,
    PURCHASE_REWARD_ITEM: (itemId: number | string) =>
      `/gamification/reward-store/purchase/${itemId}/`,

    POINTS_SUMMARY: "/gamification/points-summary/",
    MY_ITEMS: "/gamification/my-items/",
  },
  Blog: {
    POSTS: "/blog/posts/",
    adviceRequests: "/blog/advice-requests/",
  },
  COMMUNITY: {
    POSTS: "/community/posts/",
    POST_DETAIL: (id: number | string) => `/community/posts/${id}/`,
    POST_TOGGLE_LIKE: (id: number | string) =>
      `/community/posts/${id}/toggle_like/`,
    REPLIES: (postId: number | string) => `/community/posts/${postId}/replies/`,
    REPLY_TOGGLE_LIKE: (id: number | string) =>
      `/community/replies/${id}/toggle_like/`,
    TAGS: "/community/tags/",
    PARTNERS: "/community/partners/",
    PARTNER_REQUESTS: "/community/partner-requests/",
    PARTNER_REQUEST_ACCEPT: (id: number) =>
      `/community/partner-requests/${id}/accept/`,
    PARTNER_REQUEST_REJECT: (id: number) =>
      `/community/partner-requests/${id}/reject/`,
  },
};
