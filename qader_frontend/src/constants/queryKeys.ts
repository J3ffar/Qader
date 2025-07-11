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
    grades: () => [...queryKeys.user.all, "grades"] as const,

    support: {
      // <-- ADD THIS NEW SECTION
      all: () => [...queryKeys.user.all, "support"] as const,
      lists: () => [...queryKeys.user.support.all(), "lists"] as const,
      list: (filters: object = {}) =>
        [...queryKeys.user.support.lists(), filters] as const,
      details: () => [...queryKeys.user.support.all(), "details"] as const,
      detail: (id: number | string) => [...queryKeys.user.support.details(), id] as const,
      issueTypes: () => [...queryKeys.user.support.all(), "issueTypes"] as const, // <-- ADD THIS
    },
  },

  // ADDING ADMIN SECTION
  admin: {
    all: ["admin"] as const,
    users: {
      all: () => [...queryKeys.admin.all, "users"] as const,
      lists: () => [...queryKeys.admin.users.all(), "list"] as const,
      list: (filters: object) =>
        [...queryKeys.admin.users.lists(), filters] as const,
      pointLog: (userId: number | string, page: number | string) =>
        [...queryKeys.admin.users.all(), "pointLog", userId, page] as const,
      testHistory: (userId: number | string, page: number | string) =>
        [...queryKeys.admin.users.all(), "testHistory", userId, page] as const,
      statistics: (userId: number | string) =>
        [...queryKeys.admin.users.all(), "statistics", userId] as const,
    },
    userDetails: {
      all: () => [...queryKeys.admin.all, "userDetails"] as const,
      detail: (userId: number | string) =>
        [...queryKeys.admin.userDetails.all(), userId] as const,
    },
    statistics: {
      all: () => [...queryKeys.admin.all, "statistics"] as const,
      overviews: () =>
        [...queryKeys.admin.statistics.all(), "overviews"] as const,
      overview: (filters: object) =>
        [...queryKeys.admin.statistics.overviews(), filters] as const,
    },
    support: {
      all: () => [...queryKeys.admin.all, "support"] as const,
      lists: () => [...queryKeys.admin.support.all(), "lists"] as const,
      list: (filters: object) =>
        [...queryKeys.admin.support.lists(), filters] as const,
      details: () => [...queryKeys.admin.support.all(), "details"] as const,
      detail: (id: number | string) =>
        [...queryKeys.admin.support.details(), id] as const,
      replies: (id: number | string) =>
        [...queryKeys.admin.support.detail(id), "replies"] as const,
    },
    content: {
      all: () => [...queryKeys.admin.all, "content"] as const,
      // Pages
      pages: {
        all: () => [...queryKeys.admin.content.all(), "pages"] as const,
        lists: () => [...queryKeys.admin.content.pages.all(), "list"] as const,
        list: (params: object) =>
          [...queryKeys.admin.content.pages.lists(), params] as const,
        details: () =>
          [...queryKeys.admin.content.pages.all(), "details"] as const,
        detail: (slug: string) =>
          [...queryKeys.admin.content.pages.details(), slug] as const,
      },
      // FAQs
      faqs: {
        all: () => [...queryKeys.admin.content.all(), "faqs"] as const,
        categories: () =>
          [...queryKeys.admin.content.faqs.all(), "categories"] as const,
        items: () => [...queryKeys.admin.content.faqs.all(), "items"] as const,
        categoryList: () =>
          [
            ...queryKeys.admin.content.faqs.all(),
            "categories",
            "list",
          ] as const,
        itemList: (categoryId: number) =>
          [
            ...queryKeys.admin.content.faqs.all(),
            "items",
            "list",
            categoryId,
          ] as const,
      },
      homepage: {
        all: () => [...queryKeys.admin.content.all(), "homepage"] as const,
        features: () =>
          [...queryKeys.admin.content.homepage.all(), "features"] as const,
        stats: () =>
          [...queryKeys.admin.content.homepage.all(), "stats"] as const,
      },
      partners: {
        all: () => [...queryKeys.admin.content.all(), "partners"] as const,
        categories: () =>
          [...queryKeys.admin.content.partners.all(), "categories"] as const,
      },
      contact: {
        // NEW SECTION
        all: () => [...queryKeys.admin.content.all(), "contact"] as const,
        lists: () =>
          [...queryKeys.admin.content.contact.all(), "list"] as const,
        list: (filters: object) =>
          [...queryKeys.admin.content.contact.lists(), filters] as const,
      },
      // Other content types can be added here following the same pattern
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
  community: {
    all: ["community"] as const,
    posts: {
      all: () => [...queryKeys.community.all, "posts"] as const,
      lists: () => [...queryKeys.community.posts.all(), "list"] as const,
      list: (filters: object) =>
        [...queryKeys.community.posts.lists(), filters] as const,
    },
    postDetails: {
      all: () => [...queryKeys.community.all, "postDetails"] as const,
      detail: (id: number | string) =>
        [...queryKeys.community.postDetails.all(), id] as const,
      // NEW: Specific key for a post's replies
      replies: (postId: number | string, filters: object = {}) =>
        [
          ...queryKeys.community.postDetails.detail(postId),
          "replies",
          filters,
        ] as const,
    },
    tags: {
      all: () => [...queryKeys.community.all, "tags"] as const,
      lists: () => [...queryKeys.community.tags.all(), "list"] as const,
      list: (filters: object) =>
        [...queryKeys.community.tags.lists(), filters] as const,
    },
    partners: {
      all: () => [...queryKeys.community.all, "partners"] as const,
      lists: () => [...queryKeys.community.partners.all(), "list"] as const,
      list: (filters: object) =>
        [...queryKeys.community.partners.lists(), filters] as const,
    },
    partnerRequests: {
      all: () => [...queryKeys.community.all, "partnerRequests"] as const,
      lists: () =>
        [...queryKeys.community.partnerRequests.all(), "list"] as const,
      list: (filters: object) =>
        [...queryKeys.community.partnerRequests.lists(), filters] as const,
    },
  },
};
