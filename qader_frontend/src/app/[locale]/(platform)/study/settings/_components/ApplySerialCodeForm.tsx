"use client";

import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { applySerialCode } from "@/services/subscription.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { KeyRound } from "lucide-react";

const applyCodeSchema = z.object({
  serial_code: z
    .string()
    .min(1, "Serial code must be at least 1 characters")
    .max(50, "Serial code cannot be more than 50 characters"),
});

type ApplyCodeFormValues = z.infer<typeof applyCodeSchema>;

export default function ApplySerialCodeForm() {
  const t = useTranslations("Study.settings.subscriptions.applyCode");
  const queryClient = useQueryClient();

  const form = useForm<ApplyCodeFormValues>({
    resolver: zodResolver(applyCodeSchema),
    defaultValues: {
      serial_code: "",
    },
  });

  const mutation = useMutation({
    mutationFn: applySerialCode,
    onSuccess: (data) => {
      toast.success(t("toast.successTitle"), {
        description: data.detail,
      });
      // This is the key to updating the UI. It forces a refetch of the user's data.
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.USER_PROFILE_KEY[0]],
      });
      form.reset();
    },
    onError: (error) => {
      toast.error(t("toast.errorTitle"), {
        description: getApiErrorMessage(error, t("toast.errorTitle")),
      });
    },
  });

  function onSubmit(data: ApplyCodeFormValues) {
    mutation.mutate(data);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <KeyRound className="h-6 w-6 text-green-600" />
          {t("title")}
        </CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(onSubmit)}
            className="flex items-end gap-4"
          >
            <FormField
              control={form.control}
              name="serial_code"
              render={({ field }) => (
                <FormItem className="flex-grow">
                  <FormLabel>{t("form.label")}</FormLabel>
                  <FormControl>
                    <Input placeholder={t("form.placeholder")} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending
                ? t("form.buttonSaving")
                : t("form.buttonSave")}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
