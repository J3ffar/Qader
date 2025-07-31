"use client";

import React from "react";
import { useTranslations } from "next-intl";
import Image from "next/image";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Lightbulb } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useEmergencyModeStore } from "@/store/emergency.store";
import EmergencyModeActivitationForm from "./EmergencyModeActivitationForm"; // This now renders the client-approved design
import { queryKeys } from "@/constants/queryKeys";
import { startEmergencyMode } from "@/services/study.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { StartEmergencyModePayload } from "@/types/api/study.types";

export function EmergencyModeSetup() {
  const t = useTranslations("Study.emergencyMode.setup");
  const tSession = useTranslations("Study.emergencyMode.session");
  const startNewSession = useEmergencyModeStore(
    (state) => state.startNewSession
  );

  const { mutate, isPending } = useMutation({
    mutationKey: queryKeys.emergencyMode.start(),
    mutationFn: (payload: StartEmergencyModePayload) =>
      startEmergencyMode(payload),
    onSuccess: (data) => {
      toast.success(tSession("sessionStartedToast"));
      startNewSession(data.session_id, data.suggested_plan);
    },
    onError: (error) => {
      toast.error(tSession("sessionStartErrorToast"), {
        description: getApiErrorMessage(error, t("apiErrorFallback")),
      });
    },
  });

  const handleFormSubmit = (values: {
    days_until_test: number;
    available_time_hours: number;
  }) => {
    const payload: StartEmergencyModePayload = {
      ...values,
      focus_areas: ["verbal", "quantitative"],
    };
    mutate(payload);
  };

  return (
    <Card className="max-w-6xl mx-auto shadow-none bg-transparent">
      <CardHeader className="text-center">
        <CardTitle className="text-3xl font-bold">{t("title")}</CardTitle>
        <CardDescription className="text-lg text-muted-foreground">
          {t("description")}
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-8">
        <Alert>
          <Lightbulb className="h-4 w-4" />
          <AlertTitle className="font-semibold">
            {t("whatToExpectTitle")}
          </AlertTitle>
          <AlertDescription>{t("whatToExpectDescription")}</AlertDescription>
        </Alert>

        {/* The form now renders with the client-requested layout */}
        <EmergencyModeActivitationForm
          onSubmit={handleFormSubmit}
          isPending={isPending}
        />
      </CardContent>
    </Card>
  );
}
