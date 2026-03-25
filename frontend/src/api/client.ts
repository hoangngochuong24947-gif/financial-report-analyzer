import createClient from "openapi-fetch";
import type { paths } from "./generated/schema";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL;

export const apiClient = createClient<paths>({
  baseUrl: apiBaseUrl,
});
