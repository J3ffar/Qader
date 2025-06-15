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

  return (
    <>
      {/* Desktop Table View */}
      <div className="hidden rounded-xl border md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[150px]">{t("table.testType")}</TableHead>
              <TableHead>{t("table.date")}</TableHead>
              <TableHead className="text-center">
                {t("table.numQuestions")}
              </TableHead>
              <TableHead className="text-center">{t("table.score")}</TableHead>
              <TableHead className="text-center">{t("table.status")}</TableHead>
              <TableHead className="w-[240px] text-center">
                {t("table.actions")}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {attempts.map((attempt) => (
              <TableRow key={attempt.attempt_id}>
                <TableCell className="font-medium capitalize">
                  {attempt.test_type}
                </TableCell>
                <TableCell>
                  {new Date(attempt.date).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })}
                </TableCell>
                <TableCell className="text-center">
                  {attempt.num_questions}
                </TableCell>
                <TableCell className="text-center font-semibold">
                  {attempt.score_percentage !== null
                    ? `${attempt.score_percentage.toFixed(0)}%`
                    : "—"}
                </TableCell>
                <TableCell className="text-center">
                  <Badge variant={getStatusBadgeVariant(attempt.status)}>
                    {attempt.status_display}
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
