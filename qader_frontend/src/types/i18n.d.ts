// src/types/i18n.d.ts
import type enAuthMessages from "@/locales/en/auth.json";
import type enCommonMessages from "@/locales/en/common.json";
// Import types from other namespaces if you have them, e.g.:
// import type enFormsMessages from '@/locales/en/forms.json';

/**
 * Represents the complete structure of messages used by next-intl.
 * This structure should mirror the `messages` object returned in `src/i18n.ts`.
 * We use one locale (e.g., 'en') as the template for the keys,
 * assuming all other locales will have the same key structure for each namespace.
 */
export type AppMessages = {
  Auth: typeof enAuthMessages;
  Common: typeof enCommonMessages;
  // Forms: typeof enFormsMessages; // Example for another namespace
  // Add other namespaces here as defined in your src/i18n.ts
};

// This tells TypeScript that the `IntlMessages` type used by next-intl
// in your project corresponds to `AppMessages`.
// This helps with type inference for `useTranslations` and other next-intl hooks.
declare global {
  // eslint-disable-next-line @typescript-eslint/no-empty-interface
  interface IntlMessages extends AppMessages {}
}
