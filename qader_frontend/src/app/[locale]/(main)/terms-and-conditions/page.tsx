import TermsAndConditionsClient from "@/components/features/main/terms-and-conditions/TermsAndConditionsClient";
import { getLegalPagesContent } from "@/services/content.service";
import type { Metadata } from "next";

let cachedConditionsData: Awaited<
  ReturnType<typeof getLegalPagesContent>
> | null = null;
let cacheConditionsTimestamp = 0;
const CACHE_TTL = 3600 * 1000; // 1 hour
const RETRY_TTL = 60 * 1000; // retry after 1 minute if failed

export const metadata: Metadata = {
  title: "الشروط والأحكام | منصة قادر",
  description:
    "اطلع على الشروط والأحكام الخاصة بمنصة قادر التعليمية لفهم التزاماتك وحقوقك.",
};

export default async function TermsAndConditionPage() {
  const now = Date.now();
  const cacheExpired = now - cacheConditionsTimestamp > CACHE_TTL;
  const cacheRetryExpired = now - cacheConditionsTimestamp > RETRY_TTL;

  if (
    !cachedConditionsData ||
    cacheExpired ||
    (cachedConditionsData === null && cacheRetryExpired)
  ) {
    try {
      const freshData = await getLegalPagesContent();
      if (freshData && freshData.terms) {
        cachedConditionsData = freshData;
        cacheConditionsTimestamp = now;
      } else {
        console.warn("Terms content missing in fetched data.");
      }
    } catch (error) {
      console.error("Failed to fetch terms content:", error);
    }
  }
  if (!cachedConditionsData || !cachedConditionsData.terms) {
    return <p>تعذر تحميل محتوى الشروط والأحكام حالياً.</p>;
  }
  return <TermsAndConditionsClient content={cachedConditionsData.terms} />;
}
