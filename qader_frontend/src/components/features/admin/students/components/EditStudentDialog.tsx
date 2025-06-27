import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import {
  getAdminUserDetail,
  updateAdminUser,
} from "@/services/api/admin/users.service";
import { queryKeys } from "@/constants/queryKeys";
import { UpdateUserPayload } from "@/types/api/admin/users.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { setFormErrorsFromApi } from "@/utils/setFormErrorsFromApi";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";

interface EditStudentDialogProps {
  userId: number;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const formSchema = (t: any) =>
  z.object({
    full_name: z.string().min(1, { message: t("form.fullNameRequired") }),
    username: z
      .string()
      .min(1, { message: t("form.usernameRequired") })
      .optional(),
    email: z
      .string()
      .email({ message: t("form.emailInvalid") })
      .optional(),
    is_active: z.boolean(),
  });

export default function EditStudentDialog({
  userId,
  isOpen,
  onOpenChange,
}: EditStudentDialogProps) {
  const t = useTranslations("Admin.StudentManagement");
  const tCommon = useTranslations("Common");
  const queryClient = useQueryClient();

  const { data: user, isLoading: isUserLoading } = useQuery({
    queryKey: queryKeys.admin.userDetails.detail(userId),
    queryFn: () => getAdminUserDetail(userId),
    enabled: !!userId && isOpen,
  });

  const formSchemaInstance = formSchema(t);

  const form = useForm<z.infer<typeof formSchemaInstance>>({
    resolver: zodResolver(formSchemaInstance),
  });

  useEffect(() => {
    if (user) {
      form.reset({
        full_name: user.full_name,
        username: user.user.username,
        email: user.user.email,
        is_active: user.user.is_active,
      });
    }
  }, [user, form, isOpen]);

  const { mutate: updateUser, isPending } = useMutation({
    mutationFn: (data: UpdateUserPayload) => updateAdminUser(userId, data),
    onSuccess: () => {
      toast.success(t("notifications.updateSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.users.lists() as any,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.userDetails.detail(userId),
      });
      onOpenChange(false);
    },
    onError: (error) => {
      const handled = setFormErrorsFromApi(error, form.setError);
      if (!handled) {
        toast.error(t("notifications.updateError"), {
          description: getApiErrorMessage(
            error,
            t("notifications.updateError")
          ),
        });
      }
    },
  });

  function onSubmit(values: z.infer<typeof formSchemaInstance>) {
    const payload: UpdateUserPayload = {
      full_name: values.full_name,
      user: {
        username: values.username,
        email: values.email,
        is_active: values.is_active,
      },
    };
    updateUser(payload);
  }

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      form.clearErrors();
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("form.editDialogTitle")}</DialogTitle>
          <DialogDescription>
            {t("form.editDialogDescription")}
          </DialogDescription>
        </DialogHeader>
        {isUserLoading ? (
          <div className="space-y-4 py-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-6 w-24" />
          </div>
        ) : (
          <Form {...form}>
            <form
              onSubmit={form.handleSubmit(onSubmit)}
              className="space-y-4 py-4"
            >
              <FormField
                control={form.control}
                name="full_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.fullNameLabel")}</FormLabel>
                    <FormControl>
                      <Input
                        placeholder={t("form.fullNamePlaceholder")}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.usernameLabel")}</FormLabel>
                    <FormControl>
                      <Input
                        placeholder={t("form.usernamePlaceholder")}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t("form.emailLabel")}</FormLabel>
                    <FormControl>
                      <Input
                        type="email"
                        placeholder={t("form.emailPlaceholder")}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-3 shadow-sm">
                    <div className="space-y-0.5">
                      <FormLabel>{t("statuses.active")}</FormLabel>
                    </div>
                    <FormControl>
                      <Switch
                        checked={field.value}
                        onCheckedChange={field.onChange}
                      />
                    </FormControl>
                  </FormItem>
                )}
              />
              <DialogFooter>
                <DialogClose asChild>
                  <Button type="button" variant="secondary">
                    {tCommon("cancel")}
                  </Button>
                </DialogClose>
                <Button type="submit" disabled={isPending}>
                  {isPending ? tCommon("saving") : tCommon("saveChanges")}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        )}
      </DialogContent>
    </Dialog>
  );
}
