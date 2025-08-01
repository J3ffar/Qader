import PrivacyClient from "@/components/features/main/privacy/PrivacyClient";
import { getLegalPagesContent } from "@/services/content.service";
import type { Metadata } from "next";

let cachedPrivacyData: Awaited<ReturnType<typeof getLegalPagesContent>> | null =
  null;
let cachePrivacyTimestamp = 0;
const CACHE_TTL = 3600 * 1000; // 1 hour
const RETRY_TTL = 60 * 1000; // retry after 1 minute if failed

export const metadata: Metadata = {
  title: "سياسة الخصوصية | منصة قادر",
  description:
    "تعرف على سياسة الخصوصية لمنصة قادر التعليمية وكيفية التعامل مع بياناتك.",
};

export default async function PrivacyPage() {
  const now = Date.now();
  const cacheExpired = now - cachePrivacyTimestamp > CACHE_TTL;
  const cacheRetryExpired = now - cachePrivacyTimestamp > RETRY_TTL;

  if (
    !cachedPrivacyData ||
    cacheExpired ||
    (cachedPrivacyData === null && cacheRetryExpired)
  ) {
    try {
      const freshData = await getLegalPagesContent();
      if (freshData && freshData.privacy) {
        cachedPrivacyData = freshData;
        cachePrivacyTimestamp = now;
      } else {
        console.warn("Privacy content missing in fetched data.");
      }
    } catch (error) {
      console.error("Failed to fetch privacy content:", error);
    }
  }

  if (!cachedPrivacyData || !cachedPrivacyData.privacy) {
    return <p>تعذر تحميل محتوى سياسة الخصوصية حالياً.</p>;
  }

  return <PrivacyClient content={cachedPrivacyData.privacy} />;
}
