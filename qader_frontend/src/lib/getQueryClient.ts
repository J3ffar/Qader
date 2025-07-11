import { QueryClient } from "@tanstack/react-query";
import { cache } from "react";

/**
 * Creates and caches a singleton instance of QueryClient for each server-side request.
 * This prevents data from being shared between users and ensures that each
 * user gets their own fresh instance of the QueryClient.
 */
const getQueryClient = cache(() => new QueryClient());

export default getQueryClient;
