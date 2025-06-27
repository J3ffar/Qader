import { useState } from "react";
import {
  MoreHorizontal,
  Pen,
  Trash,
  List,
  Coins,
  History,
  KeyRound,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { queryKeys } from "@/constants/queryKeys";
import {
  deleteAdminUser,
  resetUserPassword,
} from "@/services/api/admin/users.service";
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
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import StudentDetailViewDialog from "./StudentDetailViewDialog";
import EditStudentDialog from "./EditStudentDialog";
import AdjustPointsDialog from "./AdjustPointsDialog";

interface StudentTableActionsProps {
  userId: number;
}

export default function StudentTableActions({
  userId,
}: StudentTableActionsProps) {
  const t = useTranslations("Admin.StudentManagement");
  const tCommon = useTranslations("Common");
  const queryClient = useQueryClient();

  const [isViewOpen, setViewOpen] = useState(false);
  const [isEditOpen, setEditOpen] = useState(false);
  const [isAdjustPointsOpen, setAdjustPointsOpen] = useState(false);
  const [isPointLogOpen, setPointLogOpen] = useState(false);
  const [isDeleteAlertOpen, setDeleteAlertOpen] = useState(false);
  const [isResetPasswordAlertOpen, setResetPasswordAlertOpen] = useState(false);

  const { mutate: deleteUserMutation, isPending: isDeleting } = useMutation({
    mutationFn: (userId: number) => deleteAdminUser(userId),
    onSuccess: () => {
      toast.success(t("notifications.deleteSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.users.lists() as any,
      });
      setDeleteAlertOpen(false);
    },
    onError: (error) =>
      toast.error(t("notifications.deleteError"), {
        description: error.message,
      }),
  });

  const { mutate: resetPasswordMutation, isPending: isResettingPassword } =
    useMutation({
      mutationFn: (userId: number) => resetUserPassword(userId),
      onSuccess: () => {
        toast.success(t("notifications.resetPasswordSuccess"));
        setResetPasswordAlertOpen(false);
      },
      onError: (error) =>
        toast.error(t("notifications.resetPasswordError"), {
          description: error.message,
        }),
    });

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-8 w-8 p-0">
            <span className="sr-only">{t("toggleMenu")}</span>
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>{t("actions")}</DropdownMenuLabel>
          <DropdownMenuItem onSelect={() => setViewOpen(true)}>
            <List className="ltr:mr-2 rtl:ml-2 h-4 w-4" /> {t("viewDetails")}
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => setEditOpen(true)}>
            <Pen className="ltr:mr-2 rtl:ml-2 h-4 w-4" /> {t("editUser")}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onSelect={() => setAdjustPointsOpen(true)}>
            <Coins className="ltr:mr-2 rtl:ml-2 h-4 w-4" /> {t("adjustPoints")}
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => setResetPasswordAlertOpen(true)}>
            <KeyRound className="ltr:mr-2 rtl:ml-2 h-4 w-4" />{" "}
            {t("resetPassword")}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            onSelect={() => setDeleteAlertOpen(true)}
            className="text-destructive focus:text-destructive"
          >
            <Trash className="ltr:mr-2 rtl:ml-2 h-4 w-4" /> {t("deleteUser")}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={isDeleteAlertOpen} onOpenChange={setDeleteAlertOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("confirmDeleteTitle")}</AlertDialogTitle>
            <AlertDialogDescription>
              {t("confirmDeleteDescription")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{tCommon("cancel")}</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteUserMutation(userId)}
              disabled={isDeleting}
            >
              {isDeleting ? tCommon("deleting") : tCommon("delete")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Reset Password Confirmation Dialog */}
      <AlertDialog
        open={isResetPasswordAlertOpen}
        onOpenChange={setResetPasswordAlertOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {t("confirmResetPasswordTitle")}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {t("confirmResetPasswordDescription")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{tCommon("cancel")}</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => resetPasswordMutation(userId)}
              disabled={isResettingPassword}
            >
              {isResettingPassword ? tCommon("sending") : t("sendResetLink")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Render the feature dialog components */}
      <StudentDetailViewDialog
        userId={userId}
        isOpen={isViewOpen}
        onOpenChange={setViewOpen}
      />
      <EditStudentDialog
        userId={userId}
        isOpen={isEditOpen}
        onOpenChange={setEditOpen}
      />
      {isAdjustPointsOpen && (
        <AdjustPointsDialog
          userId={userId}
          isOpen={isAdjustPointsOpen}
          onOpenChange={setAdjustPointsOpen}
        />
      )}
    </>
  );
}
