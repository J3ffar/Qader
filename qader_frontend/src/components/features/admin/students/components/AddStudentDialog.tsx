"use client";

import { useTranslations } from "next-intl";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import { Button } from "@/components/ui/button";
import { queryKeys } from "@/constants/queryKeys";
import { createAdminUser } from "@/services/api/admin/users.service";
import { CreateUserPayload } from "@/types/api/admin/users.types";

interface AddStudentDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

// KEY CHANGE: Removed 'role' from the schema. It will be hardcoded.
const addStudentFormSchema = (t: any) =>
  z
    .object({
      full_name: z.string().min(1, { message: t("form.fullNameRequired") }),
      username: z.string().min(1, { message: t("form.usernameRequired") }),
      email: z.string().email({ message: t("form.emailInvalid") }),
      password: z.string().min(8, { message: t("form.passwordMinLength") }),
      password_confirm: z.string().min(8, {
        message: t("form.passwordConfirmMinLength"),
      }),
    })
    .refine((data) => data.password === data.password_confirm, {
      message: t("form.passwordsMismatch"),
      path: ["password_confirm"],
    });

export default function AddStudentDialog({
  isOpen,
  onOpenChange,
}: AddStudentDialogProps) {
  const t = useTranslations("Admin.StudentManagement");
  const tCommon = useTranslations("Common");
  const queryClient = useQueryClient();

  const formSchema = addStudentFormSchema(t);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      full_name: "",
      username: "",
      email: "",
      password: "",
      password_confirm: "",
    },
  });

  const { mutate: createUser, isPending } = useMutation({
    mutationFn: (data: CreateUserPayload) => createAdminUser(data),
    onSuccess: () => {
      toast.success(t("notifications.createSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.users.lists() as any,
      });
      onOpenChange(false);
      form.reset();
    },
    onError: (error) => {
      toast.error(t("notifications.createError"), {
        description: getApiErrorMessage(error, t("notifications.createError")),
      });
    },
  });

  const onSubmit = (data: z.infer<typeof formSchema>) => {
    // KEY CHANGE: Hardcoding the role to 'student' in the payload.
    const payload: CreateUserPayload = {
      ...data,
      role: "student",
    };
    createUser(payload);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("form.addDialogTitle")}</DialogTitle>
          <DialogDescription>
            {t("form.addDialogDescription")}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="grid gap-4 py-4"
          >
            {/* Form fields are the same, except for the 'role' select which is removed */}
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
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("form.passwordLabel")}</FormLabel>
                  <FormControl>
                    <Input type="password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="password_confirm"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("form.passwordConfirmLabel")}</FormLabel>
                  <FormControl>
                    <Input type="password" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter className="pt-4">
              <DialogClose asChild>
                <Button type="button" variant="secondary">
                  {tCommon("cancel")}
                </Button>
              </DialogClose>
              <Button type="submit" disabled={isPending}>
                {isPending ? tCommon("creating") : tCommon("create")}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
