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

  LEARNING_SECTIONS: "learningSections",
  USER_TEST_ATTEMPTS: "userTestAttempts",
  USER_TEST_ATTEMPT_DETAIL: "userTestAttemptDetail", // (attemptId: number | string) => [USER_TEST_ATTEMPT_DETAIL, attemptId]
  USER_TEST_ATTEMPT_REVIEW: "userTestAttemptReview",
  // ... other query keys
};
