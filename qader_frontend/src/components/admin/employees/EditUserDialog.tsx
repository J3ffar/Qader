"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { getAdminUserDetail, updateAdminUser } from "@/services/admin.service";
import { queryKeys } from "@/constants/queryKeys";
import { UpdateAdminUserPayload } from "@/types/api/admin.types";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";

interface EditUserDialogProps {
  userId: number | null;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const formSchema = z.object({
  full_name: z.string().min(2, "Full name is required."),
  role: z.enum(["student", "teacher", "trainer", "admin", "sub_admin"]),
  is_active: z.boolean(),
});

export default function EditUserDialog({
  userId,
  isOpen,
  onOpenChange,
}: EditUserDialogProps) {
  const t = useTranslations("Admin.EmployeeManagement");
  const queryClient = useQueryClient();

  const { data: user, isLoading: isUserLoading } = useQuery({
    queryKey: queryKeys.admin.userDetails.detail(userId!),
    queryFn: () => getAdminUserDetail(userId!),
    enabled: !!userId && isOpen,
  });

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
  });

  useEffect(() => {
    if (user) {
      form.reset({
        full_name: user.full_name,
        role: user.role,
        is_active: user.user.is_active,
      });
    }
  }, [user, form]);

  const { mutate: updateUser, isPending } = useMutation({
    mutationFn: (data: UpdateAdminUserPayload) =>
      updateAdminUser(userId!, data),
    onSuccess: () => {
      toast.success("User updated successfully.");
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.users.lists(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.userDetails.detail(userId!),
      });
      onOpenChange(false);
    },
    onError: (error) => {
      toast.error("Failed to update user.", { description: error.message });
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    const payload: UpdateAdminUserPayload = {
      full_name: values.full_name,
      role: values.role,
      user: {
        is_active: values.is_active,
      },
    };
    updateUser(payload);
  }

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{t("editUser")}</DialogTitle>
        </DialogHeader>
        {isUserLoading ? (
          <div className="space-y-4 py-4">
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
                    <FormLabel>{t("table.name")}</FormLabel>
                    <FormControl>
                      <Input placeholder="User's full name" {...field} />
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
                    <FormLabel>{t("table.role")}</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a role" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {[
                          "student",
                          "teacher",
                          "trainer",
                          "admin",
                          "sub_admin",
                        ].map((role) => (
                          <SelectItem key={role} value={role}>
                            {t(`roles.${role}`)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
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
                    {t("cancel")}
                  </Button>
                </DialogClose>
                <Button type="submit" disabled={isPending}>
                  {isPending ? "Saving..." : "Save changes"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        )}
      </DialogContent>
    </Dialog>
  );
}
