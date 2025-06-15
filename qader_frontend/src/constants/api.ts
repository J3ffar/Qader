export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://qader.vip"; // Ensure this is your actual API backend
export const API_VERSION = "v1";

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: "/auth/login/",
    SIGNUP: "/auth/signup/",
    CONFIRM_EMAIL: "/auth/confirm-email/", // Note: Dynamic parts like {uidb64}/{token} are handled in service
    LOGOUT: "/auth/logout/",
    REFRESH_TOKEN: "/auth/token/refresh/",
    REQUEST_OTP: "/auth/password/reset/request-otp/",
    VERIFY_OTP: "/auth/password/reset/verify-otp/",
    RESET_PASSWORD_CONFIRM_OTP: "/auth/password/reset/confirm-otp/",
    // ... other auth endpoints
  },
  USERS: {
    ME: "/users/me/",
    COMPLETE_PROFILE: "/users/me/complete-profile/",
    CHANGE_PASSWORD: "/users/me/change-password/",
    APPLY_SERIAL_CODE: "/users/me/apply-serial-code/",
    // ... other user endpoints
  },
  STUDY: {
    STATISTICS: "/study/statistics/",
    CONVERSATIONS: "/study/conversations",
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
    BADGES_LIST: "/gamification/badges/",
    MY_BADGES: "/gamification/my-badges/",
    POINTS_LOG: "/gamification/point-log/",
    GAMIFICATION_SUMMARY: "/gamification/summary/",
  },
  // ... other domains like LEARNING, BLOG, CHALLENGES etc.
};
