export const getApiErrorMessage = (
  error: any,
  defaultMessage: string
): string => {
  console.error("Full API Error Object:", error); // Log the whole error object for inspection

  if (error?.data) {
    const errorData = error.data;
    console.log("API Error Data Content:", errorData);

    // Scenario 1: `detail` is a string (common direct message)
    if (typeof errorData.detail === "string") {
      return errorData.detail;
    }

    // Scenario 2: `detail` is an OBJECT containing `non_field_errors` (your current case)
    if (typeof errorData.detail === "object" && errorData.detail !== null) {
      if (
        Array.isArray(errorData.detail.non_field_errors) &&
        errorData.detail.non_field_errors.length > 0
      ) {
        return errorData.detail.non_field_errors.map(String).join(", ");
      }
      // You could also check for field-specific errors within errorData.detail here if needed
      // Example: if (typeof errorData.detail.some_field_error === 'string') return errorData.detail.some_field_error;
    }

    // Scenario 3: `non_field_errors` is at the top level (common DRF validation)
    if (
      Array.isArray(errorData.non_field_errors) &&
      errorData.non_field_errors.length > 0
    ) {
      return errorData.non_field_errors.map(String).join(", ");
    }

    // Scenario 4: Field-specific errors at the top level
    let fieldErrorMessages: string[] = [];
    if (typeof errorData === "object" && errorData !== null) {
      // Iterate over keys in errorData, skipping 'detail' if we've already tried to process it
      for (const key in errorData) {
        if (key === "detail" && typeof errorData.detail === "object") continue; // Already handled or will be

        if (Array.isArray(errorData[key])) {
          fieldErrorMessages = fieldErrorMessages.concat(
            errorData[key].map(String)
          );
        } else if (typeof errorData[key] === "string") {
          fieldErrorMessages.push(String(errorData[key]));
        }
      }
    }
    if (fieldErrorMessages.length > 0) {
      return fieldErrorMessages.join("; ");
    }

    // Scenario 5: If errorData is a string itself
    if (typeof errorData === "string") {
      return errorData;
    }
  }

  // Fallback to general error.message
  if (typeof error?.message === "string") {
    return error.message;
  }

  // If all else fails
  return defaultMessage;
};
