"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useTranslations } from "next-intl";

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
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Loader2, Rocket } from "lucide-react";
import { startEmergencyMode } from "@/services/study.service";
import { useEmergencyModeStore } from "@/store/emergency.store";
import { QUERY_KEYS } from "@/constants/queryKeys";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

const emergencyModeSchema = z.object({
  available_time_hours: z.coerce
    .number()
    .min(1, { message: "Must be at least 1 hour" })
    .max(24),
  focus_areas: z
    .array(z.enum(["verbal", "quantitative"]))
    .min(1, { message: "Please select at least one area to focus on." }),
  reason: z.string().optional(),
});

export function EmergencyModeSetup() {
  const t = useTranslations("Study.emergencyMode.setup");
  const startNewSession = useEmergencyModeStore(
    (state) => state.startNewSession
  );

  const form = useForm<z.infer<typeof emergencyModeSchema>>({
    resolver: zodResolver(emergencyModeSchema),
    defaultValues: {
      available_time_hours: 1,
      focus_areas: ["verbal", "quantitative"],
      reason: "",
    },
  });

  const { mutate, isPending } = useMutation({
    mutationKey: [QUERY_KEYS.START_EMERGENCY_SESSION],
    mutationFn: startEmergencyMode,
    onSuccess: (data) => {
      toast.success(t("sessionStartedToast"));
      startNewSession(data.session_id, data.suggested_plan);
    },
    onError: (error) => {
      toast.error(t("sessionStartErrorToast"), {
        description: getApiErrorMessage(error, t("sessionStartErrorToast")),
      });
    },
  });

  function onSubmit(values: z.infer<typeof emergencyModeSchema>) {
    mutate(values);
  }

  // --- THE FIX IS HERE ---
  const focusOptions = [
    { id: "verbal", label: t("verbal") },
    { id: "quantitative", label: t("quantitative") },
  ] as const; // This assertion is key!

  return (
    <Card className="mx-auto max-w-3xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Rocket className="h-6 w-6 text-primary" />
          {t("title")}
        </CardTitle>
        <CardDescription>{t("description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="available_time_hours"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("hoursLabel")}</FormLabel>
                  <FormControl>
                    <Input type="number" placeholder="e.g., 2" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="focus_areas"
              render={() => (
                <FormItem>
                  <FormLabel>{t("focusAreasLabel")}</FormLabel>
                  <div className="flex flex-col gap-4 sm:flex-row">
                    {/* Now, `item.id` will have the type "verbal" | "quantitative" */}
                    {focusOptions.map((item) => (
                      <FormField
                        key={item.id}
                        control={form.control}
                        name="focus_areas"
                        render={({ field }) => (
                          <FormItem className="flex flex-row items-start space-x-3 space-y-0 rtl:space-x-reverse">
                            <FormControl>
                              <Checkbox
                                // This line is now type-safe
                                checked={field.value?.includes(item.id)}
                                onCheckedChange={(checked) => {
                                  return checked
                                    ? field.onChange([...field.value, item.id])
                                    : field.onChange(
                                        field.value?.filter(
                                          (value) => value !== item.id
                                        )
                                      );
                                }}
                              />
                            </FormControl>
                            <FormLabel className="font-normal">
                              {item.label}
                            </FormLabel>
                          </FormItem>
                        )}
                      />
                    ))}
                  </div>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="reason"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("reasonLabel")}</FormLabel>
                  <FormControl>
                    <Textarea placeholder={t("reasonPlaceholder")} {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={isPending}>
              {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {t("startSessionButton")}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
