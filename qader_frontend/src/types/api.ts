export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Defines a flexible yet type-safe structure for API request query parameters.
 * This is used for filtering, searching, sorting, and pagination across the application.
 *
 * It uses an index signature `[key: string]` to allow any string as a key,
 * which is necessary for dynamic query parameters. The value type is a union
of all primitive types and arrays of primitives that we expect to send to the backend.
 */
export type ApiRequestParams = {
  [key: string]:
    | string
    | number
    | boolean
    | string[]
    | number[]
    | null
    | undefined;
};
