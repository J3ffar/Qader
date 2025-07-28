import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { queryKeys } from "@/constants/queryKeys";
import { adjustUserPoints } from "@/services/api/admin/users.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

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
import { Textarea } from "@/components/ui/textarea";

interface AdjustPointsDialogProps {
  userId: number;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const formSchema = (t: any) =>
  z.object({
    points_change: z.coerce
      .number()
      .int()
      .refine((val) => val !== 0, { message: t("form.pointsChangeNonZero") }),
    reason: z
      .string()
      .min(5, { message: t("form.reasonMinLength") })
      .max(255),
  });

export default function AdjustPointsDialog({
  userId,
  isOpen,
  onOpenChange,
}: AdjustPointsDialogProps) {
  const t = useTranslations("Admin.StudentManagement");
  const tCommon = useTranslations("Common");
  const queryClient = useQueryClient();
  const formSchemaInstance = formSchema(t);

  const form = useForm<z.infer<typeof formSchemaInstance>>({
    resolver: zodResolver(formSchemaInstance),
    defaultValues: { points_change: 0, reason: "" },
  });

  const { mutate: adjustPoints, isPending } = useMutation({
    mutationFn: (data: z.infer<typeof formSchemaInstance>) =>
      adjustUserPoints(userId, data),
    onSuccess: () => {
      toast.success(t("notifications.adjustPointsSuccess"));
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.users.lists() as any,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.admin.userDetails.detail(userId),
      });
      onOpenChange(false);
      form.reset();
    },
    onError: (error) => {
      toast.error(t("notifications.adjustPointsError"), {
        description: getApiErrorMessage(
          error,
          t("notifications.adjustPointsError")
        ),
      });
    },
  });

  const onSubmit = (data: z.infer<typeof formSchemaInstance>) => {
    adjustPoints(data);
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{t("form.adjustPointsTitle")}</DialogTitle>
          <DialogDescription>
            {t("form.adjustPointsDescription")}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="space-y-4 py-4"
          >
            <FormField
              control={form.control}
              name="points_change"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("form.pointsChangeLabel")}</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      placeholder="e.g. 50 or -20"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("form.reasonLabel")}</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder={t("form.reasonPlaceholder")}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
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
      </DialogContent>
    </Dialog>
  );
}
