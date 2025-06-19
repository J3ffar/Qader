import {
  ApplySerialCodePayload,
  ApplySerialCodeResponse,
  SubscriptionPlan,
} from "@/types/api/subscription.types";
import { apiClient } from "./apiClient";

export const getSubscriptionPlans = (): Promise<SubscriptionPlan[]> => {
  return apiClient<SubscriptionPlan[]>("/users/subscription-plans/", {
    isPublic: true, // Assuming plans can be viewed by anyone
  });
};

/**
 * Submits a serial code to activate a subscription for the current user.
 * @param payload - An object containing the serial_code string.
 * @returns A promise that resolves to the API response with updated subscription details.
 */
export const applySerialCode = (
  payload: ApplySerialCodePayload
): Promise<ApplySerialCodeResponse> => {
  // NOTE: Assuming this endpoint exists as per the feature requirement.
  return apiClient<ApplySerialCodeResponse>("/users/me/apply-serial-code/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
};
