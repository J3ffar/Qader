"use client";

import { useTranslations } from "next-intl";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { BookText, Calculator, BarChart3, AlertCircle } from "lucide-react";
import type { UserStatistics } from "@/types/api/study.types";

interface Props {
  performance: UserStatistics["performance_by_section"];
}

// Helper to get an icon based on section slug (can be expanded)
const getSectionIcon = (slug: string) => {
  if (slug.includes("verbal"))
    return <BookText className="h-5 w-5 text-muted-foreground" />;
  if (slug.includes("quantitative"))
    return <Calculator className="h-5 w-5 text-muted-foreground" />;
  return <BarChart3 className="h-5 w-5 text-muted-foreground" />;
};

export function SectionPerformanceBreakdown({ performance }: Props) {
  const t = useTranslations("Study.statistics.breakdown");
  const sectionSlugs = Object.keys(performance);

  if (sectionSlugs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("title")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-40 flex-col items-center justify-center gap-2 text-center text-muted-foreground">
            <AlertCircle className="h-8 w-8" />
            <p>{t("noData")}</p>
            <p className="text-sm">{t("noDataHint")}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {sectionSlugs.map((slug) => {
            const section = performance[slug];
            const subsections = Object.values(section.subsections);
            const accuracy = section.overall_accuracy ?? 0;

            return (
              <div key={slug} className="space-y-3 rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getSectionIcon(slug)}
                    <h3 className="text-lg font-semibold">{section.name}</h3>
                  </div>
                  <span className="text-lg font-bold">
                    {accuracy.toFixed(1)}%
                  </span>
                </div>
                <Progress
                  value={accuracy}
                  aria-label={`${section.name} accuracy`}
                />
                <p className="text-sm text-muted-foreground">
                  {t("overallAccuracy")}
                </p>

                {subsections.length > 0 && (
                  <Accordion type="single" collapsible className="w-full">
                    <AccordionItem value="item-1">
                      <AccordionTrigger>
                        {t("viewSubsections")}
                      </AccordionTrigger>
                      <AccordionContent>
                        <ul className="space-y-2 text-sm">
                          {subsections.map((sub) => (
                            <li
                              key={sub.name}
                              className="flex items-center justify-between rounded-md p-2 hover:bg-muted/50"
                            >
                              <span>{sub.name}</span>
                              <div className="flex items-center gap-4">
                                <span className="text-xs text-muted-foreground ltr:mr-2 rtl:ml-2">
                                  {t("attempts", { count: sub.attempts })}
                                </span>
                                <span className="w-16 text-right font-semibold">
                                  {sub.accuracy != null
                                    ? `${sub.accuracy.toFixed(1)}%`
                                    : "N/A"}
                                </span>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
