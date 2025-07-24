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
    mutationFn: (id: number) => deleteAdminQuestion(id),
    onSuccess: () => {
      toast.success("تم حذف السؤال بنجاح.");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.learning.questions.lists(),
      });
      onClose();
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "فشل حذف السؤال."));
    },
  });

  const handleDelete = () => {
    if (questionId) {
      mutation.mutate(questionId);
    }
  };

  return (
    <AlertDialog open={isOpen} onOpenChange={onClose}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>هل أنت متأكد تمامًا؟</AlertDialogTitle>
          <AlertDialogDescription>
            لا يمكن التراجع عن هذا الإجراء. سيؤدي هذا إلى حذف السؤال وبياناته
            المرتبطة به بشكل دائم.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={onClose} disabled={mutation.isPending}>
            إلغاء
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={mutation.isPending}
            className="bg-red-600 hover:bg-red-700"
          >
            {mutation.isPending ? "جاري الحذف..." : "حذف"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
