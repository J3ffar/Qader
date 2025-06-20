import {
  ApplySerialCodePayload,
  ApplySerialCodeResponse,
  CancelSubscriptionResponse,
  SubscriptionPlan,
} from "@/types/api/subscription.types";
import { apiClient } from "./apiClient";
import { API_ENDPOINTS } from "@/constants/api"; // <-- Import API_ENDPOINTS

export const getSubscriptionPlans = (): Promise<SubscriptionPlan[]> => {
  return apiClient<SubscriptionPlan[]>(API_ENDPOINTS.USERS.SUBSCRIPTION_PLANS, {
    isPublic: true,
  });
};

export const applySerialCode = (
  payload: ApplySerialCodePayload
): Promise<ApplySerialCodeResponse> => {
  return apiClient<ApplySerialCodeResponse>(
    API_ENDPOINTS.USERS.APPLY_SERIAL_CODE,
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
};

export const cancelSubscription = (): Promise<CancelSubscriptionResponse> => {
  return apiClient<CancelSubscriptionResponse>(
    API_ENDPOINTS.USERS.CANCEL_SUBSCRIPTION,
    {
      method: "POST",
    }
  );
};
