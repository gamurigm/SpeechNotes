export {};

declare global {
  interface Window {
    electronAPI?: {
      startGoogleAuth: () => Promise<{ code: string; state: string }>;
    };
  }
}
