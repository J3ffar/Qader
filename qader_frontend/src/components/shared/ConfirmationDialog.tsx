"use client";

import React from "react";
import { useTranslations } from "next-intl";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";

interface ConfirmationDialogProps {
  triggerButton: React.ReactElement<any>; // The button that opens the dialog
  title: string;
  description: string;
  confirmActionText?: string;
  cancelActionText?: string;
  onConfirm: () => void;
  isConfirming?: boolean; // To show loading state on confirm button
  confirmButtonVariant?: any;
}

const ConfirmationDialog: React.FC<ConfirmationDialogProps> = ({
  triggerButton,
  title,
  description,
  confirmActionText,
  cancelActionText,
  onConfirm,
  isConfirming = false,
  confirmButtonVariant = "destructive",
}) => {
  const tCommon = useTranslations("Common");

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>{triggerButton}</AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="text-center">{title}</AlertDialogTitle>
          <AlertDialogDescription className="ltr:text-left rtl:text-right">
            {description}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isConfirming}>
            {cancelActionText || tCommon("cancel")}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={isConfirming}
            className={
              confirmButtonVariant ? `hover:bg-${confirmButtonVariant}/90` : ""
            }
          >
            {isConfirming && (
              <Loader2 className="me-2 h-4 w-4 animate-spin rtl:me-0 rtl:ms-2" />
            )}
            {confirmActionText || tCommon("confirm")}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
};

export default ConfirmationDialog;
