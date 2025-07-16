"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useTranslations } from "next-intl";
import Image from "next/image";

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
import { CircleAlert, Send } from "lucide-react";
import { startEmergencyMode } from "@/services/study.service";
import { useEmergencyModeStore } from "@/store/emergency.store";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { queryKeys } from "@/constants/queryKeys";
import { EmergencyModeActivitationForm } from "./EmergencyModeActivitationForm";
import { Switch } from "@/components/ui/switch";

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
  const tSession = useTranslations("Study.emergencyMode.session");
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
    mutationKey: queryKeys.emergencyMode.all,
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
    <main className="flex-1 flex flex-col gap-4 max-h-fit">
      {/* Header Container */}
      <div className="w-full p-4 pb-0">
        <p className="font-semibold text-2xl">{t("title")}</p>
        <p className="text-muted-foreground">{t("description")} </p>
      </div>

      {/* Content Container */}
      <div className="flex-1 grid grid-rows-1 gap-2 w-full min-h-0">
        {/* Upper Section */}
        <Card className="w-full p-1 min-w-0 shadow-none">
          <CardContent className="flex flex-col items-center gap-0 p-0">
            <div className="w-full rounded-md p-4 flex flex-col justify-center">
              <div>
                <p className="font-semibold text-xl">
                  {t("activateEmergencyMode")}
                </p>
                <p className="text-muted-foreground">
                  {t("selectDaysAndHours")}
                </p>
              </div>
              {/* Form */}
              <EmergencyModeActivitationForm />
            </div>
            <div className="flex flex-col justify-center items-center p-4 gap-2">
              <Image
                src="/images/document.svg"
                alt="Document illustration"
                width={400}
                height={300}
                className="object-contain"
              />
              <div className="text-center space-y-2">
                <p className="font-semibold text-2xl">
                  {t("selectDaysAndHours")}
                </p>
                <p className="text-muted-foreground">{t("needToSelect")}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Lower Section */}
        <Card className="h-fit border-none shadow-none py-4">
          <CardContent className="p-0 grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-4">
            {/* Tips and focus mode */}
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between p-4 border rounded-lg">
                <span className="font-semibold">
                  {tSession("activateQuietMode")}
                </span>
                <div className="flex items-center gap-2 mt-2 sm:mt-0">
                  <span>{tSession("quietModeLabel")}</span>
                  <Switch />
                  <CircleAlert className="h-5 w-5 text-muted-foreground hover:text-inherit transition" />
                </div>
              </div>
              <div className="p-4 border rounded-lg h-full">
                <h3 className="font-bold mb-1 text-2xl">{tSession("generalTipsForYou")}</h3>
                <ul className="list-disc pr-4 space-y-1 text-sm">
                  {/* ToDo: fetch them from the backend */}
                  <li>تحتاج التقليل من التوتر.</li>
                  <li>نصيحة</li>
                  <li>نصيحة</li>
                  <li>نصيحة</li>
                  <li>نصيحة</li>
                </ul>
              </div>
            </div>
            {/* Report a problem */}
            <div className="flex flex-col justify-between border rounded-lg p-4">
              <div>
                <h2 className="font-bold text-lg mb-1">
                  {tSession("shareWithAdminLabel")}{" "}
                </h2>
                <p className="text-sm mb-4">
                  <span className="w-1 h-1 mx-1 inline-block" />
                  {tSession("stillConfusedMessage")}
                </p>
              </div>
              <form className="space-y-4 p-4 rounded-2xl shadow-sm">
                <div>
                  <label className="block mb-1 font-semibold text-gray-700">
                    {tSession("issueTypeLabel")}
                  </label>
                  <select
                    className="w-full border border-gray-200 rounded px-3 py-2 focus:outline-none"
                    defaultValue=""
                  >
                    <option value="" disabled>
                      {tSession("selectIssueTypeLabel")}
                    </option>
                    <option value="technical">
                      {tSession("issueTypeTechnical")}
                    </option>
                    <option value="other">{tSession("issueTypeOther")}</option>
                  </select>
                </div>
                <div>
                  <label className="block mb-1 font-semibold text-gray-700">
                    {tSession("requestDescriptionLabel")}
                  </label>
                  <Textarea
                    className="w-full border h-36 resize-none border-gray-200 rounded px-3 py-2 focus:outline-none"
                    placeholder={tSession("requestDescriptionPlaceholder")}
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full font-bold py-2 rounded flex items-center justify-center gap-2"
                >
                  {tSession("send")}
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            </div>
          </CardContent>
        </Card>
      </div>
    </main>

    // <Card className="mx-auto max-w-3xl">
    //   <CardHeader>
    //     <CardTitle className="flex items-center gap-2">
    //       <Rocket className="h-6 w-6 text-primary" />
    //       {t("title")}
    //     </CardTitle>
    //     <CardDescription>{t("description")}</CardDescription>
    //   </CardHeader>
    //   <CardContent>
    //     <Form {...form}>
    //       <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
    //         <FormField
    //           control={form.control}
    //           name="available_time_hours"
    //           render={({ field }) => (
    //             <FormItem>
    //               <FormLabel>{t("hoursLabel")}</FormLabel>
    //               <FormControl>
    //                 <Input type="number" placeholder="e.g., 2" {...field} />
    //               </FormControl>
    //               <FormMessage />
    //             </FormItem>
    //           )}
    //         />
    //         <FormField
    //           control={form.control}
    //           name="focus_areas"
    //           render={() => (
    //             <FormItem>
    //               <FormLabel>{t("focusAreasLabel")}</FormLabel>
    //               <div className="flex flex-col gap-4 sm:flex-row">
    //                 {/* Now, `item.id` will have the type "verbal" | "quantitative" */}
    //                 {focusOptions.map((item) => (
    //                   <FormField
    //                     key={item.id}
    //                     control={form.control}
    //                     name="focus_areas"
    //                     render={({ field }) => (
    //                       <FormItem className="flex flex-row items-start space-x-3 space-y-0 rtl:space-x-reverse">
    //                         <FormControl>
    //                           <Checkbox
    //                             // This line is now type-safe
    //                             checked={field.value?.includes(item.id)}
    //                             onCheckedChange={(checked) => {
    //                               return checked
    //                                 ? field.onChange([...field.value, item.id])
    //                                 : field.onChange(
    //                                     field.value?.filter(
    //                                       (value) => value !== item.id
    //                                     )
    //                                   );
    //                             }}
    //                           />
    //                         </FormControl>
    //                         <FormLabel className="font-normal">
    //                           {item.label}
    //                         </FormLabel>
    //                       </FormItem>
    //                     )}
    //                   />
    //                 ))}
    //               </div>
    //               <FormMessage />
    //             </FormItem>
    //           )}
    //         />
    //         <FormField
    //           control={form.control}
    //           name="reason"
    //           render={({ field }) => (
    //             <FormItem>
    //               <FormLabel>{t("reasonLabel")}</FormLabel>
    //               <FormControl>
    //                 <Textarea placeholder={t("reasonPlaceholder")} {...field} />
    //               </FormControl>
    //               <FormMessage />
    //             </FormItem>
    //           )}
    //         />
    //         <Button type="submit" className="w-full" disabled={isPending}>
    //           {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
    //           {t("startSessionButton")}
    //         </Button>
    //       </form>
    //     </Form>
    //   </CardContent>
    // </Card>
  );
}
