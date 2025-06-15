"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { UseMutationResult } from "@tanstack/react-query";
import {
  ListChecks,
  ListX,
  Loader2,
  MoreVertical,
  RotateCw,
  PlayCircle,
  Ban,
  Info,
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
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";

import { PATHS } from "@/constants/paths";
import {
  UserTestAttemptList,
  UserTestAttemptStartResponse,
} from "@/types/api/study.types";

type TestAttemptActionsProps = {
  attempt: UserTestAttemptList;
  onRetake: (attemptId: number) => void;
  isRetaking: boolean;
  retakeAttemptId: number | null;
  cancelAttemptMutation: UseMutationResult<void, Error, number, unknown>;
  cancellingAttemptId: number | null;
};

const TestAttemptActions = ({
  attempt,
  onRetake,
  isRetaking,
  retakeAttemptId,
  cancelAttemptMutation,
  cancellingAttemptId,
}: TestAttemptActionsProps) => {
  const t = useTranslations("Study.tests.list.actions");

  const isThisAttemptRetaking =
    isRetaking && retakeAttemptId === attempt.attempt_id;
  const isThisAttemptCancelling =
    cancelAttemptMutation.isPending &&
    cancellingAttemptId === attempt.attempt_id;

  return (
    <TooltipProvider>
      {(() => {
        switch (attempt.status) {
          case "started":
            return (
              <div className="flex flex-col justify-center gap-2 sm:flex-row">
                <Tooltip>
                  <TooltipTrigger asChild>
                    {/* The disabled button is wrapped in a span for the tooltip to work correctly */}
                    <span tabIndex={0}>
                      <Button asChild size="sm" disabled>
                        {/* We use a Link so it's ready once enabled */}
                        <Link
                          href={PATHS.STUDY.TESTS.ATTEMPT(attempt.attempt_id)}
                        >
                          <PlayCircle className="me-2 h-4 w-4" />
                          {t("continueTest")}
                        </Link>
                      </Button>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{t("continueTestTooltip")}</p>
                  </TooltipContent>
                </Tooltip>

                <ConfirmationDialog
                  triggerButton={
                    <Button
                      variant="destructive"
                      size="sm"
                      disabled={isThisAttemptCancelling}
                    >
                      {isThisAttemptCancelling ? (
                        <Loader2 className="me-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Ban className="me-2 h-4 w-4" />
                      )}
                      {t("cancelTest")}
                    </Button>
                  }
                  title={t("cancelDialog.title")}
                  description={t("cancelDialog.description", {
                    attemptId: attempt.attempt_id,
                  })}
                  confirmActionText={t("cancelDialog.confirmButton")}
                  onConfirm={() =>
                    cancelAttemptMutation.mutate(attempt.attempt_id)
                  }
                  isConfirming={isThisAttemptCancelling}
                  confirmButtonVariant="destructive"
                />
              </div>
            );

          case "completed":
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
                <DropdownMenuContent align="start">
                  <DropdownMenuItem asChild>
                    <Link href={PATHS.STUDY.TESTS.REVIEW(attempt.attempt_id)}>
                      <ListChecks className="me-2 h-4 w-4" />
                      <span>{t("review")}</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link
                      href={PATHS.STUDY.TESTS.REVIEW(attempt.attempt_id, true)}
                    >
                      <ListX className="me-2 h-4 w-4" />
                      <span>{t("reviewIncorrect")}</span>
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onSelect={() => onRetake(attempt.attempt_id)}
                  >
                    <RotateCw className="me-2 h-4 w-4" />
                    <span>{t("retake")}</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            );

          case "abandoned":
            return (
              <Tooltip>
                <TooltipTrigger asChild>
                  <span
                    tabIndex={0}
                    className="flex items-center gap-1.5 text-sm italic text-muted-foreground"
                  >
                    <Info size={14} /> {attempt.status_display}
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{t("abandonedTooltip")}</p>
                </TooltipContent>
              </Tooltip>
            );

          default:
            return (
              <span className="text-sm italic text-muted-foreground">
                {attempt.status_display}
              </span>
            );
        }
      })()}
    </TooltipProvider>
  );
};

export default TestAttemptActions;
