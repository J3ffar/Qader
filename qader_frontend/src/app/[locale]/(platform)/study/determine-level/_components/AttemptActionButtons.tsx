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
import { UserTestAttemptList } from "@/types/api/study.types";

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
  const t = useTranslations("Study.determineLevel.actions");

  const isCancellingThisAttempt =
    cancelAttemptMutation.isPending &&
    cancelAttemptMutation.variables === attempt.attempt_id;

  // Use a single TooltipProvider at the root of the component
  return (
    <TooltipProvider>
      {(() => {
        switch (attempt.status) {
          case "started":
            return (
              <div className="flex flex-col justify-center gap-2 sm:flex-row">
                <Button size="sm" asChild>
                  <Link
                    href={PATHS.STUDY.DETERMINE_LEVEL.ATTEMPT(
                      attempt.attempt_id
                    )}
                  >
                    <PlayCircle className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                    {t("continueTest")}
                  </Link>
                </Button>

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
                  isConfirming={isCancellingThisAttempt}
                  confirmButtonVariant="destructive"
                />
              </div>
            );

          case "completed":
            return (
              <div className="flex justify-center">
                <Button variant="outline" size="sm" asChild>
                  <Link
                    href={PATHS.STUDY.DETERMINE_LEVEL.REVIEW(
                      attempt.attempt_id
                    )}
                  >
                    <FileText className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                    {t("reviewTest")}
                  </Link>
                </Button>
              </div>
            );

          case "abandoned":
            return (
              <div className="flex justify-center">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span tabIndex={-1}>
                      <Button variant="outline" size="sm" disabled>
                        <Info className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                        {t("viewDetails")}
                      </Button>
                    </span>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{t("abandonedTooltip")}</p>
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
