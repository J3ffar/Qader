"use client";

import { useTranslations } from "next-intl";
import { UseMutationResult } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableHeader,
  TableRow,
  TableHead,
  TableBody,
  TableCell,
} from "@/components/ui/table";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { UserTestAttemptList } from "@/types/api/study.types";
import TestAttemptActions from "./TestAttemptActions";
import { get } from "http";

type TestAttemptsListProps = {
  attempts: UserTestAttemptList[];
  onRetake: (attemptId: number) => void;
  isRetaking: boolean;
  retakeAttemptId: number | null;
  cancelAttemptMutation: UseMutationResult<void, Error, number, unknown>;
  cancellingAttemptId: number | null;
};

const TestAttemptsList = ({
  attempts,
  onRetake,
  isRetaking,
  retakeAttemptId,
  cancelAttemptMutation,
  cancellingAttemptId,
}: TestAttemptsListProps) => {
  const t = useTranslations("Study.tests.list");

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case "completed":
        return "default";
      case "started":
        return "secondary";
      case "abandoned":
        return "destructive";
      default:
        return "outline";
    }
  };
  const getGradeVariant = (score: number): string => {
    if (score >= 90) {
      return "bg-[#E3FFEF] text-[#27AE60]";
    } else if (score >= 50) {
      return "bg-[#FFF4D7] text-[#E6B11D]";
    } else {
      return "bg-[#FFDFDF] text-[#F34B4B]";
    }
  };
  const getGrade = (score: number): string => {
    if (score >= 90) {
      return t("table.performance.excellent");
    } else if (score >= 50) {
      return t("table.performance.good");
    } else {
      return t("table.performance.poor");
    }
  };
  return (
    <>
      {/* Desktop Table View */}
      <div className="hidden rounded-t-xl border md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-center">{t("table.date")}</TableHead>
              <TableHead className="text-center">
                {t("table.numQuestions")}
              </TableHead>
              <TableHead className="text-center">
                {t("table.percentage")}
              </TableHead>
              <TableHead className="text-center">
                {t("table.performance.quantitative")}
              </TableHead>
              <TableHead className="text-center">
                {t("table.performance.verbal")}
              </TableHead>
              <TableHead className="text-center">
                {t("table.actions")}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {attempts.map((attempt) => (
              <TableRow key={attempt.attempt_id}>
                <TableCell className="text-center border-x">
                  {(() => {
                    const date = new Date(attempt.date);
                    return `${date.getDate()}/${date.getMonth() + 1}/${
                      date.getFullYear() % 100
                    }`;
                  })()}
                </TableCell>
                <TableCell className="text-center border-x">
                  {attempt.num_questions}
                </TableCell>
                <TableCell className="text-center border-x">
                  {attempt.score_percentage !== null
                    ? `${attempt.score_percentage.toFixed(0)}%`
                    : "—"}
                </TableCell>
                <TableCell className="text-center border-x">
                  <Badge
                    className={getGradeVariant(
                      attempt.performance?.overall || 0
                    )}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-current me-1 inline-block" />
                    {getGrade(attempt.performance?.overall || 0)}
                  </Badge>
                </TableCell>

                <TableCell className="text-center border-x">
                  <Badge
                    className={getGradeVariant(
                      attempt.performance?.verbal || 0
                    )}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-current me-1 inline-block" />
                    {getGrade(attempt.performance?.verbal || 0)}
                  </Badge>
                </TableCell>
                <TableCell className="text-center">
                  <TestAttemptActions
                    attempt={attempt}
                    onRetake={onRetake}
                    isRetaking={isRetaking}
                    retakeAttemptId={retakeAttemptId}
                    cancelAttemptMutation={cancelAttemptMutation}
                    cancellingAttemptId={cancellingAttemptId}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile Accordion View */}
      <div className="space-y-3 md:hidden">
        <Accordion type="single" collapsible className="w-full">
          {attempts.map((attempt) => (
            <AccordionItem
              value={`item-${attempt.attempt_id}`}
              key={attempt.attempt_id}
              className="rounded-lg border dark:border-gray-700"
            >
              <AccordionTrigger className="p-4 hover:no-underline">
                <div className="flex w-full items-center justify-between">
                  <div className="text-start rtl:text-right">
                    <p className="font-medium capitalize">
                      {attempt.test_type}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(attempt.date).toLocaleDateString()}
                    </p>
                  </div>
                  <span className="text-lg font-bold">
                    {attempt.score_percentage !== null
                      ? `${attempt.score_percentage.toFixed(0)}%`
                      : "—"}
                  </span>
                </div>
              </AccordionTrigger>
              <AccordionContent className="p-4 pt-0">
                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">
                      {t("table.status")}
                    </span>
                    <Badge variant={getStatusBadgeVariant(attempt.status)}>
                      {attempt.status_display}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">
                      {t("table.numQuestions")}
                    </span>
                    <span>{attempt.num_questions}</span>
                  </div>
                  <div className="mt-3 flex justify-end">
                    <TestAttemptActions
                      attempt={attempt}
                      onRetake={onRetake}
                      isRetaking={isRetaking}
                      retakeAttemptId={retakeAttemptId}
                      cancelAttemptMutation={cancelAttemptMutation}
                      cancellingAttemptId={cancellingAttemptId}
                    />
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </>
  );
};

export default TestAttemptsList;
