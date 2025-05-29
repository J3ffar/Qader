// src/constants/api.ts
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "https://api.qader.vip"; // Ensure this is your actual API backend
export const API_VERSION = "v1";

// Example of a more structured way to define endpoints if they become numerous
// export const API_ENDPOINTS = {
//   AUTH: {
//     LOGIN: "/auth/login/",
//     SIGNUP: "/auth/signup/",
//     // ... other auth endpoints
//   },
//   USERS: {
//     ME: "/users/me/",
//     // ... other user endpoints
//   }
//   // ... other domains
// };
