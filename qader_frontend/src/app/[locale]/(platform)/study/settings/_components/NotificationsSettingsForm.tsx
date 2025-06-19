"use client";

import { z } from "zod";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";

import { useAuthStore } from "@/store/auth.store";
import { updateUserProfile } from "@/services/auth.service";
import type { UserProfile } from "@/types/api/user.types";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

import { Button } from "@/components/ui/button";
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
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";

const notificationsSchema = z.object({
  notify_reminders_enabled: z.boolean(),
  upcoming_test_date: z.string().nullable().optional(),
  study_reminder_time: z.string().nullable().optional(),
  dark_mode_auto_enabled: z.boolean(),
  dark_mode_auto_time_start: z.string().nullable().optional(),
  dark_mode_auto_time_end: z.string().nullable().optional(),
});

type NotificationsFormValues = z.infer<typeof notificationsSchema>;

interface NotificationsSettingsFormProps {
  user: UserProfile;
}

export default function NotificationsSettingsForm({
  user,
}: NotificationsSettingsFormProps) {
  const t = useTranslations("Study.settings.notifications");
  const queryClient = useQueryClient();
  const { updateUserProfile: updateUserInStore } = useAuthStore();

  const form = useForm<NotificationsFormValues>({
    resolver: zodResolver(notificationsSchema),
    defaultValues: {
      notify_reminders_enabled: user.notify_reminders_enabled,
      upcoming_test_date: user.upcoming_test_date || "",
      study_reminder_time: user.study_reminder_time
        ? user.study_reminder_time.substring(0, 5)
        : "",
      dark_mode_auto_enabled: user.dark_mode_auto_enabled,
      dark_mode_auto_time_start: user.dark_mode_auto_time_start
        ? user.dark_mode_auto_time_start.substring(0, 5)
        : "",
      dark_mode_auto_time_end: user.dark_mode_auto_time_end
        ? user.dark_mode_auto_time_end.substring(0, 5)
        : "",
    },
  });

  const mutation = useMutation({
    mutationFn: (data: Partial<NotificationsFormValues>) =>
      updateUserProfile(data),
    onSuccess: (updatedUser) => {
      toast.success(t("toast.success"));
      updateUserInStore(updatedUser);
      queryClient.invalidateQueries({
        queryKey: [QUERY_KEYS.USER_PROFILE_KEY[0], user.id],
      });
      form.reset(form.getValues()); // Resets dirty state after successful save
    },
    onError: (error) => {
      toast.error(t("toast.error"), {
        description: getApiErrorMessage(error, t("toast.error")),
      });
    },
  });

  function onSubmit(data: NotificationsFormValues) {
    mutation.mutate(data);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("title")}</CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            {/* Study Reminders */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium">{t("reminders.title")}</h3>
              <FormField
                control={form.control}
                name="notify_reminders_enabled"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">
                        {t("reminders.enableLabel")}
                      </FormLabel>
                      <FormDescription>
                        {t("reminders.enableDescription")}
                      </FormDescription>
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
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="upcoming_test_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("reminders.testDateLabel")}</FormLabel>
                      <FormControl>
                        <Input
                          type="date"
                          {...field}
                          value={field.value || ""}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="study_reminder_time"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("reminders.reminderTimeLabel")}</FormLabel>
                      <FormControl>
                        <Input
                          type="time"
                          {...field}
                          value={field.value || ""}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </div>
            </div>

            <Separator />

            {/* Dark Mode */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium">{t("darkMode.title")}</h3>
              <FormField
                control={form.control}
                name="dark_mode_auto_enabled"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">
                        {t("darkMode.autoEnableLabel")}
                      </FormLabel>
                      <FormDescription>
                        {t("darkMode.autoEnableDescription")}
                      </FormDescription>
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
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="dark_mode_auto_time_start"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("darkMode.startTimeLabel")}</FormLabel>
                      <FormControl>
                        <Input
                          type="time"
                          {...field}
                          value={field.value || ""}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="dark_mode_auto_time_end"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>{t("darkMode.endTimeLabel")}</FormLabel>
                      <FormControl>
                        <Input
                          type="time"
                          {...field}
                          value={field.value || ""}
                        />
                      </FormControl>
                    </FormItem>
                  )}
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={!form.formState.isDirty || mutation.isPending}
              >
                {mutation.isPending ? t("buttons.saving") : t("buttons.save")}
              </Button>
            </div>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
