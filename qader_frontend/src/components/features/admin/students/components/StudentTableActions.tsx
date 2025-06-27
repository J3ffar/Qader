import { useState } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  MoreHorizontal,
  Pencil,
  Trash2,
  Eye,
  Coins,
  History,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import { deleteAdminUser } from "@/services/api/admin/users.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { queryKeys } from "@/constants/queryKeys";
import EditStudentDialog from "./EditStudentDialog";

interface StudentTableActionsProps {
  userId: number;
}

export default function StudentTableActions({
  userId,
}: StudentTableActionsProps) {
  const t = useTranslations("Admin.StudentManagement");
  const tCommon = useTranslations("Common");
  const queryClient = useQueryClient();

  const [isEditDialogOpen, setEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const { mutate: deleteUser, isPending: isDeleting } = useMutation({
    mutationFn: () => deleteAdminUser(userId),
    onSuccess: () => {
      toast.success(t("notifications.deleteSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.users.lists() as any,
      });
    },
    onError: (error) => {
      toast.error(t("notifications.deleteError"), {
        description: getApiErrorMessage(error, t("notifications.deleteError")),
      });
    },
    onSettled: () => setDeleteDialogOpen(false),
  });

  return (
    <>
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
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
              onClick={() => deleteUser()}
              disabled={isDeleting}
            >
              {isDeleting ? tCommon("deleting") : tCommon("delete")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <EditStudentDialog
        userId={userId}
        isOpen={isEditDialogOpen}
        onOpenChange={setEditDialogOpen}
      />

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-8 w-8 p-0">
            <span className="sr-only">{t("toggleMenu")}</span>
            <MoreHorizontal className="h-4 w-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuLabel>{t("actions")}</DropdownMenuLabel>
          <DropdownMenuItem onClick={() => {}} disabled>
            <Eye className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
            {t("viewDetails")}
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => setEditDialogOpen(true)}>
            <Pencil className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
            {t("editUser")}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => {}} disabled>
            <Coins className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
            {t("adjustPoints")}
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => {}} disabled>
            <History className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
            {t("viewPointLog")}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-red-600 focus:text-red-600 dark:focus:text-red-500"
            onClick={() => setDeleteDialogOpen(true)}
          >
            <Trash2 className="ltr:mr-2 rtl:ml-2 h-4 w-4" />
            {t("deleteUser")}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </>
  );
}
