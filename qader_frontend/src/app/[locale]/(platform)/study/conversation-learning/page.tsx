import React from "react";
import { getTranslations } from "next-intl/server";
import { ConversationLearningClient } from "@/components/features/platform/study/conversation-learning/ConversationLearningClient";

export async function generateMetadata() {
  const t = await getTranslations("Study.conversationalLearning");
  return {
    title: t("title"),
  };
}

export default function ConversationLearningPage() {
  return (
    <div className="container mx-auto">
      <ConversationLearningClient />
    </div>
  );
}
