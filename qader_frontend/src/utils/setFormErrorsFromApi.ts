import { FieldValues, UseFormSetError } from "react-hook-form";

/**
 * A type guard to check if the error is a structured API validation error.
 * @param error - The error object from TanStack Query's onError.
 */
function isApiValidationError(
  error: any
): error is { data: Record<string, any>; status: number } {
  return (
    error &&
    typeof error === "object" &&
    error.status === 400 &&
    error.data &&
    typeof error.data === "object"
  );
}

/**
 * Maps nested Django REST Framework error keys to flat form field names.
 * Example: 'user.username' from API maps to 'username' in the form.
 */
const fieldMap: Record<string, string> = {
  "user.username": "username",
  "user.email": "email",
  full_name: "full_name",
  // Add other mappings here as needed
};

/**
 * Parses a Django REST Framework validation error and sets errors on a React Hook Form instance.
 * @param error - The error object from TanStack Query.
 * @param setError - The setError function from a useForm hook.
 * @returns {boolean} - True if errors were successfully parsed and set, false otherwise.
 */
export function setFormErrorsFromApi<T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>
): boolean {
  if (!isApiValidationError(error)) {
    return false;
  }

  let errorsHandled = false;

  // Flatten nested errors (e.g., { user: { username: [...] } })
  const flattenErrors = (
    obj: Record<string, any>,
    prefix = ""
  ): Record<string, string[]> => {
    return Object.keys(obj).reduce((acc, k) => {
      const pre = prefix.length ? prefix + "." : "";
      if (typeof obj[k] === "object" && !Array.isArray(obj[k])) {
        Object.assign(acc, flattenErrors(obj[k], pre + k));
      } else {
        acc[pre + k] = obj[k];
      }
      return acc;
    }, {} as Record<string, string[]>);
  };

  const apiErrors = flattenErrors(error.data);

  Object.entries(apiErrors).forEach(([key, messages]) => {
    const formFieldName = fieldMap[key] as keyof T;
    const errorMessage = Array.isArray(messages)
      ? messages[0]
      : String(messages);

    if (formFieldName && errorMessage) {
      setError(formFieldName as any, {
        type: "server",
        message: errorMessage,
      });
      errorsHandled = true;
    }
  });

  return errorsHandled;
}
