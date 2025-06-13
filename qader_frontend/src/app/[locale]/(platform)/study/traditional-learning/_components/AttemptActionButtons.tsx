"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { UseMutationResult } from "@tanstack/react-query";
import { PlayCircle, FileText, Ban, Loader2, Info } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import ConfirmationDialog from "@/components/shared/ConfirmationDialog";

import { PATHS } from "@/constants/paths";
import type { UserTestAttemptList } from "@/types/api/study.types";

type AttemptActionButtonsProps = {
  attempt: UserTestAttemptList;
  cancelAttemptMutation: UseMutationResult<
    void,
    Error,
    string | number,
    unknown
  >;
};

export const AttemptActionButtons = ({
  attempt,
  cancelAttemptMutation,
}: AttemptActionButtonsProps) => {
  // Use translations specific to traditional learning actions
  const t = useTranslations("Study.traditionalLearning.list.actions");

  const isCancellingThisAttempt =
    cancelAttemptMutation.isPending &&
    cancelAttemptMutation.variables === attempt.attempt_id;

  return (
    <TooltipProvider>
      {(() => {
        switch (attempt.status) {
          case "started":
            return (
              <div className="flex flex-col justify-center gap-2 sm:flex-row">
                {/* Continue Session button */}
                <Button asChild size="sm">
                  <Link
                    href={PATHS.STUDY.TRADITIONAL_LEARNING.SESSION(
                      attempt.attempt_id
                    )}
                  >
                    <PlayCircle className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                    {t("continueSession")}
                  </Link>
                </Button>

                {/* Cancel Session button with confirmation */}
                <ConfirmationDialog
                  triggerButton={
                    <Button
                      variant="destructive"
                      size="sm"
                      disabled={isCancellingThisAttempt}
                    >
                      {isCancellingThisAttempt ? (
                        <Loader2 className="me-2 h-4 w-4 animate-spin rtl:me-0 rtl:ms-2" />
                      ) : (
                        <Ban className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                      )}
                      {t("cancelSession")}
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
                  isConfirming={isCancellingThisAttempt}
                  confirmButtonVariant="destructive"
                />
              </div>
            );

          case "completed":
            return (
              <div className="flex justify-center">
                {/* Review Session button */}
                <Button variant="outline" size="sm" asChild>
                  <Link
                    href={PATHS.STUDY.TRADITIONAL_LEARNING.REVIEW(
                      attempt.attempt_id
                    )}
                  >
                    <FileText className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                    {t("reviewSession")}
                  </Link>
                </Button>
              </div>
            );

          case "abandoned":
            return (
              <div className="flex justify-center">
                {/* View Details button (disabled with tooltip for abandoned) */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span tabIndex={-1}>
                      <Button variant="outline" size="sm" disabled>
                        <Info className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                        {t("viewDetails")}{" "}
                        {/* Reusing viewDetails from level determine if it fits, or add a specific one */}
                      </Button>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    {/* Add specific tooltip for traditional abandoned sessions if needed */}
                    <p>{t("abandonedTooltip")}</p>{" "}
                    {/* Reusing abandonedTooltip from level determine */}
                  </TooltipContent>
                </Tooltip>
              </div>
            );

          default:
            return null;
        }
      })()}
    </TooltipProvider>
  );
};
