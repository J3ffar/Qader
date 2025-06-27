export const queryKeys = {
  // --- AUTH ---
  auth: {
    all: ["auth"] as const,
    login: () => [...queryKeys.auth.all, "login"] as const,
    signup: () => [...queryKeys.auth.all, "signup"] as const,
    confirmEmail: (uidb64: string, token: string) =>
      [...queryKeys.auth.all, "confirmEmail", uidb64, token] as const,
    requestOtp: () => [...queryKeys.auth.all, "requestOtp"] as const,
    verifyOtp: () => [...queryKeys.auth.all, "verifyOtp"] as const,
    resetPassword: () => [...queryKeys.auth.all, "resetPassword"] as const,
  },

  // --- USER ---
  user: {
    all: ["user"] as const,
    profile: (userId: number | null) =>
      [...queryKeys.user.all, "profile", userId] as const, // For /users/me
    completeProfile: () => [...queryKeys.user.all, "completeProfile"] as const,
    subscription: () => [...queryKeys.user.all, "subscription"] as const, // For /users/me
  },

  // ADDING ADMIN SECTION
  admin: {
    all: ["admin"] as const,
    users: {
      all: () => [...queryKeys.admin.all, "users"] as const,
      lists: () => [...queryKeys.admin.users.all(), "list"] as const,
      list: (filters: object) =>
        [...queryKeys.admin.users.lists(), filters] as const,
      pointLog: (userId: number | string) =>
        [...queryKeys.admin.users.all(), userId] as const,
      testHistory: (userId: number | string) =>
        [...queryKeys.admin.users.all(), userId] as const,
      statistics: (userId: number | string) =>
        [...queryKeys.admin.users.all(), userId] as const,
    },
    userDetails: {
      all: () => [...queryKeys.admin.all, "userDetails"] as const,
      detail: (userId: number | string) =>
        [...queryKeys.admin.userDetails.all(), userId] as const,
    },
  },

  // --- NOTIFICATIONS ---
  notifications: {
    all: ["notifications"] as const,
    list: (filters: object) =>
      [...queryKeys.notifications.all, "list", filters] as const,
    unreadCount: () => [...queryKeys.notifications.all, "unreadCount"] as const,
  },

  // --- GAMIFICATION ---
  gamification: {
    all: ["gamification"] as const,
    rewardStoreItems: () =>
      [...queryKeys.gamification.all, "rewardStore"] as const,
    pointsSummary: (userId: number | null) =>
      [...queryKeys.gamification.all, "pointsSummary", userId] as const,
    studyDaysLog: (userId: number | null) =>
      [...queryKeys.gamification.all, "studyDaysLog", userId] as const,
    points: (filters: object) =>
      [...queryKeys.gamification.all, "points", filters] as const,
    studyDays: (filters: object) =>
      [...queryKeys.gamification.all, "studyDays", filters] as const,
  },

  // --- STUDY & TESTS ---
  study: {
    all: ["study"] as const,
    statistics: (filters: object) =>
      [...queryKeys.study.all, "statistics", filters] as const,
  },

  tests: {
    all: ["tests"] as const,
    lists: () => [...queryKeys.tests.all, "lists"] as const,
    list: (filters: object) => [...queryKeys.tests.lists(), filters] as const,
    details: () => [...queryKeys.tests.all, "details"] as const,
    detail: (attemptId: number | string) =>
      [...queryKeys.tests.details(), attemptId] as const,
    review: (attemptId: number | string) =>
      [...queryKeys.tests.detail(attemptId), "review"] as const,
    completionResult: (attemptId: number | string) =>
      [...queryKeys.tests.detail(attemptId), "completionResult"] as const,
  },

  // --- CONVERSATIONAL LEARNING ---
  conversations: {
    all: ["conversations"] as const,
    session: (sessionId: number) =>
      [...queryKeys.conversations.all, "session", sessionId] as const,
    messages: (sessionId: number) =>
      [...queryKeys.conversations.session(sessionId), "messages"] as const,
  },

  // --- EMERGENCY MODE ---
  emergencyMode: {
    all: ["emergencyMode"] as const,
    session: (sessionId: number) =>
      [...queryKeys.emergencyMode.all, "session", sessionId] as const,
    questions: (sessionId: number) =>
      [...queryKeys.emergencyMode.session(sessionId), "questions"] as const,
    submitAnswer: (sessionId: number, questionId: number) =>
      [
        ...queryKeys.emergencyMode.questions(sessionId),
        "answer",
        questionId,
      ] as const,
  },

  // --- LEARNING SECTIONS ---
  learning: {
    all: ["learning"] as const,
    sections: (filters: object) =>
      [...queryKeys.learning.all, "sections", filters] as const,
    sectionDetail: (slug: string) =>
      [...queryKeys.learning.all, "section", slug] as const,
  },
  challenges: {
    all: ["challenges"] as const,
    lists: () => [...queryKeys.challenges.all, "lists"] as const,
    list: (filters: object) =>
      [...queryKeys.challenges.lists(), filters] as const,
    details: () => [...queryKeys.challenges.all, "details"] as const,
    detail: (id: number | string) =>
      [...queryKeys.challenges.details(), id] as const,
    types: () => [...queryKeys.challenges.all, "types"] as const,
  },
};
