import { isAxiosError } from "axios";

/**
 * Extracts a user-friendly error message from an API error object.
 * Handles various common Django Rest Framework error formats, including nested ones.
 *
 * @param error The error object, typically from a failed API call (e.g., from TanStack Query).
 * @param defaultMessage A fallback message to use if no specific message can be extracted.
 * @returns A string containing the best available error message.
 */
export const getApiErrorMessage = (
  error: unknown,
  defaultMessage: string
): string => {
  // For debugging in development, it's always useful to see the raw error.
  if (process.env.NODE_ENV === "development") {
    console.error("Full API Error Object:", error);
  }

  // TanStack Query now often wraps the original error in its own object.
  // Axios errors are common, so we check for the `response` property.
  const errorData = isAxiosError(error)
    ? error.response?.data
    : (error as any)?.data;

  if (!errorData) {
    // Fallback for non-API errors or network issues
    if (error instanceof Error) {
      return error.message;
    }
    return defaultMessage;
  }

  // --- Start of DRF-specific error parsing ---

  // Scenario 1: `detail` is an array of strings
  // Example: { "detail": ["Not enough questions found."] }
  if (Array.isArray(errorData.detail) && errorData.detail.length > 0) {
    return errorData.detail.map(String).join("\n");
  }

  // Scenario 2: `detail` is a single string
  // Example: { "detail": "Invalid credentials provided." }
  if (typeof errorData.detail === "string") {
    return errorData.detail;
  }

  // Scenario 3 (NEW): `detail` is an OBJECT containing validation errors
  // Example: { "detail": { "non_field_errors": ["Active practice already exists."] } }
  if (typeof errorData.detail === "object" && errorData.detail !== null) {
    const detailObject = errorData.detail;
    if (
      Array.isArray(detailObject.non_field_errors) &&
      detailObject.non_field_errors.length > 0
    ) {
      return detailObject.non_field_errors.map(String).join("\n");
    }
  }

  // Scenario 4: `non_field_errors` for form-level validation (at the top level)
  // Example: { "non_field_errors": ["The two password fields didn't match."] }
  if (
    Array.isArray(errorData.non_field_errors) &&
    errorData.non_field_errors.length > 0
  ) {
    return errorData.non_field_errors.map(String).join("\n");
  }

  // Scenario 5: Field-specific errors at the top level
  // Example: { "email": ["Enter a valid email address."], "password": ["This field may not be blank."] }
  let fieldErrorMessages: string[] = [];
  if (typeof errorData === "object" && errorData !== null) {
    for (const key in errorData) {
      if (key === "detail" || key === "non_field_errors") continue;

      const message = errorData[key];
      if (Array.isArray(message)) {
        fieldErrorMessages = fieldErrorMessages.concat(message.map(String));
      } else if (typeof message === "string") {
        fieldErrorMessages.push(message);
      }
    }
  }

  if (fieldErrorMessages.length > 0) {
    return fieldErrorMessages.join("\n");
  }

  // --- End of DRF-specific error parsing ---

  // Fallback to the default message if no specific error was parsed
  return defaultMessage;
};
