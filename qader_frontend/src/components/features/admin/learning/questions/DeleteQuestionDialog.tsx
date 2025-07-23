"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { queryKeys } from "@/constants/queryKeys";
import { deleteAdminQuestion } from "@/services/api/admin/learning.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

interface DeleteQuestionDialogProps {
  isOpen: boolean;
  onClose: () => void;
  questionId: number | null;
}

export function DeleteQuestionDialog({
  isOpen,
  onClose,
  questionId,
}: DeleteQuestionDialogProps) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => deleteAdminQuestion(questionId!),
    onSuccess: () => {
      toast.success("Question deleted successfully.");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.questions.lists(),
      });
      onClose();
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to delete question."));
    },
  });

  const handleDelete = () => {
    if (questionId) {
      mutation.mutate();
    }
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone. This will permanently delete the
            question and its associated data.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onClose} disabled={mutation.isPending}>
            Cancel
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={mutation.isPending}
            className="bg-red-600 hover:bg-red-700"
          >
            {mutation.isPending ? "Deleting..." : "Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
