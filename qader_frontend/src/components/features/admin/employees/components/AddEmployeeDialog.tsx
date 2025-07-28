"use client";

import { useState } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { queryKeys } from "@/constants/queryKeys";
import { createAdminUser } from "@/services/api/admin/users.service";
import { CreateUserPayload } from "@/types/api/admin/users.types";

interface AddEmployeeDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

const addEmployeeFormSchema = (t: any) =>
  z
    .object({
      full_name: z.string().min(1, { message: t("form.fullNameRequired") }),
      username: z.string().min(1, { message: t("form.usernameRequired") }),
      email: z.string().email({ message: t("form.emailInvalid") }),
      role: z.enum(["admin", "sub_admin", "teacher", "trainer"], {
        message: t("form.roleRequired"),
      }),
      password: z.string().min(8, { message: t("form.passwordMinLength") }),
      password_confirm: z.string().min(8, {
        message: t("form.passwordConfirmMinLength"),
      }),
    })
    .refine((data) => data.password === data.password_confirm, {
      message: t("form.passwordsMismatch"),
      path: ["password_confirm"],
    });

export default function AddEmployeeDialog({
  isOpen,
  onOpenChange,
}: AddEmployeeDialogProps) {
  const t = useTranslations("Admin.EmployeeManagement");
  const tCommon = useTranslations("Common");
  const queryClient = useQueryClient();

  const formSchema = addEmployeeFormSchema(t);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      full_name: "",
      username: "",
      email: "",
      role: "teacher", // Default role
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
    createUser(data);
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
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("form.roleLabel")}</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder={t("form.rolePlaceholder")} />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="admin">{t("roles.admin")}</SelectItem>
                      <SelectItem value="sub_admin">
                        {t("roles.sub_admin")}
                      </SelectItem>
                      <SelectItem value="teacher">
                        {t("roles.teacher")}
                      </SelectItem>
                      <SelectItem value="trainer">
                        {t("roles.trainer")}
                      </SelectItem>
                    </SelectContent>
                  </Select>
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
