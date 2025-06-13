"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import type { UserStatistics } from "@/types/api/study.types";
import { PATHS } from "@/constants/paths";

interface Props {
  tests: UserStatistics["test_history_summary"];
}

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
  const locale = useLocale();

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("testType")}</TableHead>
              <TableHead className="text-center">{t("score")}</TableHead>
              <TableHead className="text-right">{t("action")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tests.slice(0, 5).map((test) => (
              <TableRow key={test.attempt_id}>
                <TableCell>
                  <p className="font-medium">{test.type}</p>
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
                    <Link
                      href={PATHS.STUDY.DETERMINE_LEVEL.REVIEW(test.attempt_id)}
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
      </CardContent>
    </Card>
  );
}
