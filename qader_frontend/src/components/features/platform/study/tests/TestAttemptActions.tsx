// src/components/features/platform/study/tests/TestAttemptActions.tsx
"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import {
  ListChecks,
  ListX,
  Loader2,
  MoreVertical,
  RotateCw,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import { PATHS } from "@/constants/paths";
import { UserTestAttemptList } from "@/types/api/study.types";

type TestAttemptActionsProps = {
  attempt: UserTestAttemptList;
  onRetake: (attemptId: number) => void;
  isRetaking: boolean;
  retakeAttemptId: number | null;
};

const TestAttemptActions = ({
  attempt,
  onRetake,
  isRetaking,
  retakeAttemptId,
}: TestAttemptActionsProps) => {
  const t = useTranslations("Study.tests.list.actions");

  const isThisAttemptRetaking =
    isRetaking && retakeAttemptId === attempt.attempt_id;

  if (attempt.status !== "completed") {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <span className="text-sm italic text-muted-foreground">
              {t("inProgress")}
            </span>
          </TooltipTrigger>
          <TooltipContent>
            <p>{t("inProgressTooltip")}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="h-8 w-8 p-0"
          disabled={isThisAttemptRetaking}
        >
          <span className="sr-only">{t("openMenu")}</span>
          {isThisAttemptRetaking ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <MoreVertical className="h-4 w-4" />
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem asChild>
          <Link href={PATHS.STUDY.TESTS.REVIEW(attempt.attempt_id)}>
            <ListChecks className="me-2 h-4 w-4" />
            <span>{t("review")}</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href={PATHS.STUDY.TESTS.REVIEW(attempt.attempt_id, true)}>
            <ListX className="me-2 h-4 w-4" />
            <span>{t("reviewIncorrect")}</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => onRetake(attempt.attempt_id)}>
          <RotateCw className="me-2 h-4 w-4" />
          <span>{t("retake")}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default TestAttemptActions;
