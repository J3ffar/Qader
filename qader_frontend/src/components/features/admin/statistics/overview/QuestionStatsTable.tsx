// src/components/features/admin/statistics/overview/QuestionStatsTable.tsx
import Link from "next/link";
import { useTranslations } from "next-intl";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { type QuestionStat } from "@/types/api/admin/statistics.types";

interface QuestionStatsTableProps {
  title: string;
  data: QuestionStat[];
}

export function QuestionStatsTable({ title, data }: QuestionStatsTableProps) {
  const t = useTranslations("Admin.AdminStatistics");
  const tCore = useTranslations("Core");

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <TooltipProvider>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[60%] ps-4 rtl:ps-0 rtl:pe-4">
                    {t("question")}
                  </TableHead>
                  <TableHead className="text-center">
                    {t("attemptCount")}
                  </TableHead>
                  <TableHead className="text-center">
                    {t("accuracyRate")}
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data && data.length > 0 ? (
                  data.map((q) => (
                    <TableRow key={q.id}>
                      <TableCell className="font-medium max-w-sm">
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Link
                              href={`/admin/questions/${q.id}`}
                              className="hover:underline truncate block"
                            >
                              {q.question_text}
                            </Link>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p className="max-w-md">{q.question_text}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TableCell>
                      <TableCell className="text-center">
                        {q.attempt_count}
                      </TableCell>
                      <TableCell className="text-center">
                        {q.accuracy_rate?.toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell
                      colSpan={3}
                      className="h-24 text-center text-muted-foreground"
                    >
                      {tCore("noResultsFound")}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </TooltipProvider>
      </CardContent>
    </Card>
  );
}
