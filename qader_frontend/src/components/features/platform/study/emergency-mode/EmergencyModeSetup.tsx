"use client";

import React, { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import Image from "next/image";

import { Card, CardContent } from "@/components/ui/card";
import { CircleAlert, Send } from "lucide-react";
import { useEmergencyModeStore } from "@/store/emergency.store";
import EmergencyModeActivitationForm from "./EmergencyModeActivitationForm";
import { Switch } from "@/components/ui/switch";
import { useParams } from "next/navigation";
import ReportProblemForm from "./ReportProblemForm";
import { Label } from "@/components/ui/label";
import { useMutation } from "@tanstack/react-query";
import { queryKeys } from "@/constants/queryKeys";
import {
  startEmergencyMode,
  updateEmergencySession,
} from "@/services/study.service";
import { toast } from "sonner";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";

export function EmergencyModeSetup() {
  const { locale } = useParams();
  const dir = locale === "en" ? "ltr" : "rtl";
  const t = useTranslations("Study.emergencyMode.setup");
  const tSession = useTranslations("Study.emergencyMode.session");
  const [generalTips, setGeneralTips] = useState<string[]>([]);
  const {
    sessionId,
    suggestedPlan,
    questions,
    currentQuestionIndex,
    isSessionActive,
    isCalmModeActive,
    isSharedWithAdmin,
    startNewSession,
    setQuestions,
    goToNextQuestion,
    endSession,
    setCalmMode,
    setSharedWithAdmin,
  } = useEmergencyModeStore();

  // For activating the emergency mode
  const { mutate, isPending } = useMutation({
    mutationKey: queryKeys.emergencyMode.all,
    mutationFn: startEmergencyMode,
    onSuccess: (data) => {
      toast.success(tSession("sessionStartedToast"));
      startNewSession(data.session_id, data.suggested_plan);
    },
    onError: (error) => {
      toast.error(tSession("sessionStartErrorToast"), {
        description: getApiErrorMessage(error, tSession("sessionStartErrorToast")),
      });
    },
  });

  // For updating the calm mode
  const { mutate: updateSettings } = useMutation({
    mutationKey: queryKeys.emergencyMode.session(sessionId as number),
    mutationFn: (payload: {
      calm_mode_active?: boolean;
      shared_with_admin?: boolean;
    }) => updateEmergencySession({ sessionId: sessionId!, payload }),
    onSuccess: (data) => {
      toast.success(tSession("settingsUpdatedToast"));
      // Sync local store state with the response from the server
      setCalmMode(data.calm_mode_active);
      setSharedWithAdmin(data.shared_with_admin);
    },
    onError: (error) =>
      toast.error(tSession("settingsUpdateErrorToast"), {
        description: getApiErrorMessage(error, tSession("settingsUpdateErrorToast")),
      }),
  });
  console.log("sessionId:", sessionId);
  console.log("calm_mode_active:", isCalmModeActive);
  useEffect(() => {
    // Fetch general tips from the backend or any other source
    // For now, use dummy data
    const fetchedTips = [
      "تحتاج التقليل من التوتر.",
      "نصيحة 1",
      "نصيحة 2",
      "نصيحة 3",
      "نصيحة 4",
    ];
    setGeneralTips(fetchedTips);
  }, []);

  const focusOptions = [
    { id: "verbal", label: t("verbal") },
    { id: "quantitative", label: t("quantitative") },
  ] as const;

  // TODO: handle the toggle for calm mode
  const handleCalmModeToggle = (checked: boolean) => {
    setCalmMode(checked); // Optimistic UI update
    updateSettings({ calm_mode_active: checked });
  };
  return (
    <main className="flex-1 flex flex-col gap-4 max-h-fit" dir={dir}>
      {/* Header Container */}
      <div className="w-full p-4 pb-0">
        <p className="font-semibold text-2xl">{t("title")}</p>
        <p className="text-muted-foreground">{t("description")} </p>
      </div>

      {/* Content Container */}
      <div className="flex-1 grid grid-rows-1 gap-2 w-full min-h-0">
        {/* Upper Section */}
        <Card
          className="w-full p-1 min-w-0 shadow-none dark:bg-[#0A1739]"
          dir={dir}
        >
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
              <EmergencyModeActivitationForm onSubmit={mutate} />
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
        <Card
          className="h-fit border-none shadow-none py-4 bg-inherit"
          dir={dir}
        >
          <CardContent className="p-0 grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-4">
            <div className="flex flex-col gap-4">
              {/* Focus Mode */}
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between p-4 border rounded-lg dark:bg-[#0A1739]">
                <span className="font-semibold">
                  {tSession("activateQuietMode")}
                </span>
                <div className="flex items-center gap-2 mt-2 sm:mt-0">
                  <Label htmlFor="calm-mode">{tSession("calmModeLabel")}</Label>
                  <Switch
                    id="calm-mode"
                    checked={isCalmModeActive}
                    onCheckedChange={handleCalmModeToggle}
                  />
                  <CircleAlert className="h-5 w-5 text-muted-foreground hover:text-inherit transition" />
                </div>
              </div>
              {/* Tips */}
              <div className="p-4 border rounded-lg h-full dark:bg-[#0A1739]">
                <h3 className="font-bold mb-1 text-2xl">
                  {tSession("generalTipsForYou")}
                </h3>
                <ul className="list-disc pr-4 space-y-1 text-sm">
                  {/* ToDo: fetch them from the backend */}
                  {generalTips.map((tip, index) => (
                    <li key={index} className="text-muted-foreground">
                      {tip}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            {/* Report a problem */}
            <div className="flex flex-col justify-between border rounded-lg p-4 dark:bg-[#0A1739]">
              <div>
                <h2 className="font-bold text-lg mb-1">
                  {tSession("shareWithAdminLabel")}{" "}
                </h2>
                <p className="text-sm mb-4">
                  <span className="w-1 h-1 mx-1 inline-block" />
                  {tSession("stillConfusedMessage")}
                </p>
              </div>
              <ReportProblemForm />
            </div>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
