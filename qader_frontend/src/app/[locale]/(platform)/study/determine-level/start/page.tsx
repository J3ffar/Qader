import React from "react";
import { useTranslations } from "next-intl";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import StartLevelAssessmentForm from "@/components/features/platform/study/determine-level/StartLevelAssessmentForm";

const StartLevelAssessmentPage = () => {
  const t = useTranslations("Study.determineLevel.startForm");

  return (
    <div className="container mx-auto max-w-4xl p-4 md:p-6 lg:p-8 dark:bg-[#081028]">
      <h1 className="mb-2 text-center text-3xl font-bold">{t("pageTitle")}</h1>
      <p className="mx-auto mb-8 max-w-2xl text-center text-muted-foreground">
        {t("pageDescription")}
      </p>
      <StartLevelAssessmentForm />
    </div>
  );
};

export default StartLevelAssessmentPage;
