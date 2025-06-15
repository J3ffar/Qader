import React from "react";
import { useTranslations } from "next-intl";
import { BookOpenCheck } from "lucide-react";
import StartTestForm from "@/components/features/platform/study/tests/StartTestForm";

const StartTestPage = () => {
  const t = useTranslations("Study.tests.startForm");

  return (
    <div className="container mx-auto max-w-4xl p-4 md:p-6 lg:p-8">
      <div className="text-center">
        <BookOpenCheck className="mx-auto h-12 w-12 text-primary" />
        <h1 className="mt-4 text-3xl font-bold tracking-tight">
          {t("pageTitle")}
        </h1>
        <p className="mx-auto mt-2 max-w-2xl text-lg text-muted-foreground">
          {t("pageDescription")}
        </p>
      </div>
      <div className="mt-10">
        <StartTestForm />
      </div>
    </div>
  );
};

export default StartTestPage;
