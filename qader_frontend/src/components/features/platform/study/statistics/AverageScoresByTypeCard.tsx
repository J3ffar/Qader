"use client";

import { useTranslations } from "next-intl";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { UserStatistics } from "@/types/api/study.types";

interface Props {
  scoresByType: UserStatistics["average_scores_by_test_type"];
}

export function AverageScoresByTypeCard({ scoresByType }: Props) {
  const t = useTranslations("Study.statistics.averageScores");
  const tCommon = useTranslations("Common");
  const scoreEntries = Object.values(scoresByType);

  if (scoreEntries.length === 0) {
    return null; // Don't render the card if there's no data
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("table.type")}</TableHead>
                <TableHead className="text-center">
                  {t("table.count")}
                </TableHead>
                <TableHead className="text-center">
                  {t("table.score")}
                </TableHead>
                <TableHead className="text-center">
                  {t("table.verbal")}
                </TableHead>
                <TableHead className="text-center">
                  {t("table.quantitative")}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {scoreEntries.map((entry) => (
                <TableRow key={entry.attempt_type_value}>
                  <TableCell className="font-medium">
                    {tCommon(`testTypes.${entry.attempt_type_value}`)}
                  </TableCell>
                  <TableCell className="text-center">
                    {entry.test_count}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant="secondary">
                      {entry.average_score?.toFixed(0) ?? "N/A"}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">
                    {entry.average_verbal_score?.toFixed(0) ?? "N/A"}%
                  </TableCell>
                  <TableCell className="text-center">
                    {entry.average_quantitative_score?.toFixed(0) ?? "N/A"}%
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
