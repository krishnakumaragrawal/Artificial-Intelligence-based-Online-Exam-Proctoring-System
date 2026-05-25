declare global {
  interface Window {
    __PROCTORING_CONFIG__?: {
      API_BASE_URL?: string;
    };
  }
}

export const API_BASE_URL =
  window.__PROCTORING_CONFIG__?.API_BASE_URL ?? import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
