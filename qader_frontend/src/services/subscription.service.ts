import { SubscriptionPlan } from "@/types/api/subscription.types";
import { apiClient } from "./apiClient";

export const getSubscriptionPlans = (): Promise<SubscriptionPlan[]> => {
  return apiClient<SubscriptionPlan[]>("/users/subscription-plans/", {
    isPublic: true, // Assuming plans can be viewed by anyone
  });
};
