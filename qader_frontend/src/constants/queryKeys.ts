export const QUERY_KEYS = {
  USER: "user",
  LOGIN: "login",
  SIGNUP: "signup",
  CONFIRM_EMAIL: ["confirmEmail"],
  COMPLETE_PROFILE: ["completeProfile"],
  REQUEST_OTP_KEY: ["requestPasswordOtp"],
  VERIFY_OTP_KEY: ["verifyPasswordOtp"],
  RESET_PASSWORD_KEY: ["resetPasswordWithOtp"],

  NOTIFICATIONS_LIST: "notificationsList",
  NOTIFICATIONS_UNREAD_COUNT: "notificationsUnreadCount",
  MARK_NOTIFICATIONS_READ: "markNotificationsRead", // For mutation
  MARK_ALL_NOTIFICATIONS_READ: "markAllNotificationsRead", // For mutation
  REWARD_STORE_ITEMS: "rewardStoreItems",
  WEEKLY_POINTS_SUMMARY: "weeklyPointsSummary",
  STUDY_DAYS_LOG: "studyDaysLog",
  // ... other query keys
};
