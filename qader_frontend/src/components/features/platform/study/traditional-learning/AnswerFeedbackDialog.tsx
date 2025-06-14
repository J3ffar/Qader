"use client";

import React from "react";
import { useTranslations } from "next-intl";
import { CheckCircle, XCircle, Lightbulb } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

export interface FeedbackData {
  isCorrect: boolean;
  correctAnswerText: string;
  explanation: string | null;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  feedback: FeedbackData | null;
}

export const AnswerFeedbackDialog: React.FC<Props> = ({
  isOpen,
  onClose,
  feedback,
}) => {
  const t = useTranslations("Study.traditionalLearning.session");

  if (!feedback) {
    return null;
  }

  return (
    <AlertDialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle
            className={cn(
              "flex items-center text-2xl font-bold",
              feedback.isCorrect ? "text-green-600" : "text-red-600"
            )}
          >
            {feedback.isCorrect ? (
              <CheckCircle className="me-3 h-8 w-8" />
            ) : (
              <XCircle className="me-3 h-8 w-8" />
            )}
            {feedback.isCorrect ? t("correct") : t("incorrect")}
          </AlertDialogTitle>
          {!feedback.isCorrect && (
            <AlertDialogDescription className="pt-2 text-base">
              {t("correctAnswerWas")}{" "}
              <strong className="text-foreground">
                {feedback.correctAnswerText}
              </strong>
            </AlertDialogDescription>
          )}
        </AlertDialogHeader>

        {feedback.explanation && (
          <>
            <Separator className="my-4" />
            <div className="space-y-2">
              <h3 className="flex items-center text-lg font-semibold">
                <Lightbulb className="me-2 h-5 w-5 text-yellow-500" />
                {t("explanation")}
              </h3>
              <div className="max-h-48 overflow-y-auto rounded-md bg-muted/50 p-3 text-sm text-muted-foreground">
                {feedback.explanation}
              </div>
            </div>
          </>
        )}
        <AlertDialogFooter className="mt-4">
          {/* *** THE CHANGE IS HERE *** */}
          <AlertDialogAction onClick={onClose} className="w-full">
            {t("continue")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};
