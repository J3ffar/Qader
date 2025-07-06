import ConditionsClient from "@/components/features/main/conditions/ConditionsClient";
import { getLegalPagesContent } from "@/services/content.service";
import type { Metadata } from "next";

// Add metadata for better SEO
export const metadata: Metadata = {
  title: "الشروط والأحكام وسياسة الخصوصية | منصة قادر",
  description:
    "اطلع على الشروط والأحكام وسياسة الخصوصية الخاصة بمنصة قادر التعليمية لضمان فهم كامل لحقوقك وواجباتك.",
};

export default async function ConditionsPage() {
  // Data is fetched once on the server when the page is requested.
  const data = await getLegalPagesContent();

  // The fetched data is passed as a prop to the client component.
  return <ConditionsClient initialData={data} />;
}
