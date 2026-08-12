import { apiRequest } from "./client";
import type { SearchResponse } from "../types";

export function globalSearch(query: string): Promise<SearchResponse> {
  return apiRequest<SearchResponse>(`/search?q=${encodeURIComponent(query)}&limit=6`);
}
