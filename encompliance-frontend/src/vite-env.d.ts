/// <reference types="vite/client" />

/*
  Description: TypeScript declaration file for Vite environment variables and import metadata.
  Purpose: Ensures type safety and IntelliSense for environment variables used throughout the frontend codebase.
*/

interface ImportMetaEnv {
  readonly VITE_BACKEND_URL: string;
  readonly VITE_API_BASE_URL: string;
  // add more environment variables as needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
