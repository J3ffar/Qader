"use client";

import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CardFooter } from "@/components/ui/card";
import type { UserStatistics } from "@/types/api/study.types";
import { PATHS } from "@/constants/paths";

interface Props {
  tests: UserStatistics["test_history_summary"];
}

/**
 * Determines the correct review page URL based on the test type.
 * @param typeValue - The API slug for the test type (e.g., 'level_assessment').
 * @param attemptId - The ID of the test attempt.
 * @returns The correct URL string for the review page.
 */
const getReviewLinkForTest = (typeValue: string, attemptId: number): string => {
  switch (typeValue) {
    case "level_assessment":
      return PATHS.STUDY.DETERMINE_LEVEL.REVIEW(attemptId);
    case "practice":
    case "simulation":
      return PATHS.STUDY.TESTS.REVIEW(attemptId);
    case "traditional":
      return PATHS.STUDY.TRADITIONAL_LEARNING.REVIEW(attemptId);
    // As a fallback, link to the generic test history list.
    // We can update this if a generic "details" page is added later.
    default:
      return PATHS.STUDY.TESTS.LIST;
  }
};

const getScoreVariant = (
  score: number | null
): "outline" | "secondary" | "destructive" | "default" => {
  if (score === null) return "default";
  if (score >= 75) return "outline";
  if (score >= 50) return "secondary";
  return "destructive";
};

export function RecentTestsTable({ tests }: Props) {
  const t = useTranslations("Study.statistics.recentTests");
  const tCommon = useTranslations("Common");
  const locale = useLocale();

  return (
    <>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("testType")}</TableHead>
              <TableHead className="text-center">{t("score")}</TableHead>
              <TableHead className="text-right">{t("action")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tests.map((test) => (
              <TableRow key={test.attempt_id}>
                <TableCell>
                  <p className="font-medium">
                    {tCommon(`testTypes.${test.type_value}` as any, {
                      defaultMessage: test.type,
                    })}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(test.date).toLocaleDateString(locale, {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </p>
                </TableCell>
                <TableCell className="text-center">
                  <Badge variant={getScoreVariant(test.overall_score)}>
                    {test.overall_score !== null
                      ? `${test.overall_score.toFixed(0)}%`
                      : "N/A"}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Button asChild variant="ghost" size="sm">
                    {/* The href is now dynamically generated */}
                    <Link
                      href={getReviewLinkForTest(
                        test.type_value,
                        test.attempt_id
                      )}
                    >
                      {t("review")}{" "}
                      <ArrowRight className="h-4 w-4 ltr:ml-2 rtl:mr-2 rtl:rotate-180" />
                    </Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <CardFooter className="justify-center border-t px-6 pt-6">
        <Button asChild variant="outline" className="w-full">
          {/* This path can be added to PATHS.ts later for consistency */}
          <Link href={"/study/history"}>{t("viewAllHistory")}</Link>
        </Button>
      </CardFooter>
    </>
  );
}
