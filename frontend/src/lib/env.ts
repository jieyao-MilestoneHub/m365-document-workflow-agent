// Public, non-sensitive config only (this bundle ships to the browser).
// The API base URL is the single configurable endpoint; default to the local FastAPI.
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";
