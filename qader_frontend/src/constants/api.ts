export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://qader.vip"; // Ensure this is your actual API backend
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
    DAILY_POINTS_SUMMARY: "/gamification/points-summary/daily/",
    STUDY_DAYS: "/gamification/study-days/",
    // Adding placeholders for other gamification endpoints that might exist or be added soon
    BADGES_LIST: "/gamification/badges/",
    MY_BADGES: "/gamification/my-badges/",
    POINTS_LOG: "/gamification/point-log/",
    GAMIFICATION_SUMMARY: "/gamification/summary/",
  },
};
