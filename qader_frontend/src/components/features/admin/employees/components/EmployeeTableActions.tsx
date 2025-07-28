"use client";

import { useState } from "react";
import { List, MoreHorizontal, Pen, Trash } from "lucide-react";
import { useTranslations } from "next-intl";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { queryKeys } from "@/constants/queryKeys";
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
import { deleteAdminUser } from "@/services/api/admin/users.service";

interface EmployeeTableActionsProps {
  userId: number;
  onView: () => void;
  onEdit: () => void;
}

export default function EmployeeTableActions({
  userId,
  onView,
  onEdit,
}: EmployeeTableActionsProps) {
  const t = useTranslations("Admin.EmployeeManagement");
  const queryClient = useQueryClient();

  const [isDeleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const { mutate: deleteUserMutation, isPending } = useMutation({
    mutationFn: deleteAdminUser,
    onSuccess: () => {
      toast.success(t("notifications.deleteSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.users.lists(),
      });
      setDeleteDialogOpen(false);
    },
    onError: (error) => {
      toast.error(t("notifications.deleteError"), {
        description: error.message,
      });
    },
  });

  return (
    <>
      <DropdownMenu modal={false}>
        <DropdownMenuTrigger asChild>
          <Button aria-haspopup="true" size="icon" variant="ghost">
            <MoreHorizontal className="h-4 w-4" />
            <span className="sr-only">{t("toggleMenu")}</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start">
          <DropdownMenuLabel>{t("actions")}</DropdownMenuLabel>
          <DropdownMenuItem onSelect={onView}>
            <List className="h-4 w-4 rtl:ml-2 ltr:mr-2" />
            {t("viewDetails")}
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={onEdit}>
            <Pen className="h-4 w-4 rtl:ml-2 ltr:mr-2" />
            {t("editUser")}
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="text-destructive focus:text-destructive"
            onSelect={() => setDeleteDialogOpen(true)}
          >
            <Trash className="h-4 w-4 rtl:ml-2 ltr:mr-2" />
            {t("deleteUser")}
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{t("confirmDeleteTitle")}</AlertDialogTitle>
            <AlertDialogDescription>
              {t("confirmDeleteDescription")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>{t("cancel")}</AlertDialogCancel>
            <AlertDialogAction
              disabled={isPending}
              onClick={() => deleteUserMutation(userId)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isPending ? t("deleting") : t("delete")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
