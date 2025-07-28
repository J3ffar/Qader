// src/app/[locale]/(platform)/study/admin-support/page.tsx
import { UserSupportPage } from "@/components/features/platform/support/UserSupportPage";
import { getFaqPageContent } from "@/services/content.service";

export default async function SupportPage() {
  // We can pre-fetch the FAQ data on the server for faster initial load.
  const faqData = await getFaqPageContent();

  return <UserSupportPage initialFaqData={faqData} />;
}
