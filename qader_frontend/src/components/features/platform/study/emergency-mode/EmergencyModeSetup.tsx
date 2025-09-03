"use client";
import React, { useEffect, useRef } from "react";
import { useTranslations } from "next-intl";
import Image from "next/image";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Lightbulb, MessageSquareWarning } from "lucide-react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useEmergencyModeStore } from "@/store/emergency.store";
import EmergencyModeActivitationForm from "./EmergencyModeActivitationForm";
import { queryKeys } from "@/constants/queryKeys";
import { startEmergencyMode } from "@/services/study.service";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import { StartEmergencyModePayload } from "@/types/api/study.types";
import ReportProblemForm from "./ReportProblemForm";

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger);

// Validation constants
const MAX_HOURS = 16;
const MAX_DAYS = 14;
const MIN_DAYS = 1;

export function EmergencyModeSetup() {
  const t = useTranslations("Study.emergencyMode.setup");
  const tSession = useTranslations("Study.emergencyMode.session");
  
  // Refs for animation targets t()
  const containerRef:any = useRef<HTMLDivElement>(null);
  const mainCardRef:any = useRef<HTMLDivElement>(null);
  const reportCardRef:any = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const descriptionRef = useRef<HTMLParagraphElement>(null);
  const alertRef = useRef<HTMLDivElement>(null);
  const formContainerRef = useRef<HTMLDivElement>(null);

  const startNewSession = useEmergencyModeStore(
    (state) => state.startNewSession
  );

  const { mutate, isPending } = useMutation({
    mutationKey: queryKeys.emergencyMode.start(),
    mutationFn: (payload: StartEmergencyModePayload) =>
      startEmergencyMode(payload),
    onSuccess: (data) => {
      // Success animation - just a subtle scale
      gsap.to(mainCardRef.current, {
        scale: 1.02,
        duration: 0.3,
        yoyo: true,
        repeat: 1,
        ease: "power2.out"
      });
      
      toast.success("لقد بدأت الجلسة بنجاح");
      startNewSession(data.session_id, data.suggested_plan);
    },
    onError: (error) => {
      // Error shake animation
      gsap.to(mainCardRef.current, {
        keyframes: {
          "0%": { x: -10 },
          "10%": { x: 10 },
          "20%": { x: -8 },
          "30%": { x: 8 },
          "40%": { x: -6 },
          "50%": { x: 6 },
          "60%": { x: -4 },
          "70%": { x: 4 },
          "80%": { x: -2 },
          "90%": { x: 2 },
          "100%": { x: 0 }
        },
        duration: 0.6,
        ease: "power2.out"
      });
      
      toast.error(tSession("sessionStartErrorToast"), {
        description: getApiErrorMessage(error, t("apiErrorFallback")),
      });
    },
  });

  const validateFormValues = (values: {
    days_until_test: number;
    available_time_hours: number;
  }): boolean => {
    // Validate days
    if (values.days_until_test < MIN_DAYS) {
      toast.error("خطأ في التحقق", {
        description: "يجب أن يكون عدد الأيام المتبقية للامتحان يوم واحد على الأقل",
      });
      return false;
    }

    if (values.days_until_test > MAX_DAYS) {
      toast.error("خطأ في التحقق", {
        description: `لا يمكن أن يتجاوز عدد الأيام المتبقية للامتحان ${MAX_DAYS} يوم`,
      });
      return false;
    }

    // Validate hours
    if (values.available_time_hours > MAX_HOURS) {
      toast.error("خطأ في التحقق", {
        description: `لا يمكن أن تتجاوز ساعات الدراسة المتاحة ${MAX_HOURS} ساعة في اليوم`,
      });
      return false;
    }

    if (values.available_time_hours <= 0) {
      toast.error("خطأ في التحقق", {
        description: "يجب أن تكون ساعات الدراسة المتاحة أكثر من صفر",
      });
      return false;
    }

    return true;
  };

  const handleFormSubmit = (values: {
    days_until_test: number;
    available_time_hours: number;
  }) => {
    // Validate form values before proceeding
    if (!validateFormValues(values)) {
      // Error shake animation for validation failure
      gsap.to(formContainerRef.current, {
        keyframes: {
          "0%": { x: -5 },
          "10%": { x: 5 },
          "20%": { x: -4 },
          "30%": { x: 4 },
          "40%": { x: -3 },
          "50%": { x: 3 },
          "60%": { x: -2 },
          "70%": { x: 2 },
          "80%": { x: -1 },
          "90%": { x: 1 },
          "100%": { x: 0 }
        },
        duration: 0.4,
        ease: "power2.out"
      });
      return;
    }

    // Submit animation - just a subtle scale
    gsap.to(formContainerRef.current, {
      scale: 0.98,
      duration: 0.2,
      ease: "power2.out",
      onComplete: () => {
        gsap.to(formContainerRef.current, {
          scale: 1,
          duration: 0.3,
          ease: "back.out(1.7)"
        });
      }
    });

    const payload: StartEmergencyModePayload = {
      ...values,
      focus_areas: ["verbal", "quantitative"],
    };
    mutate(payload);
  };

  const {
    sessionId,
    suggestedPlan,
    questions,
    currentQuestionIndex,
    isCalmModeActive,
    setQuestions,
    setCalmMode,
    setCompleting,
    completeSession,
    endSession,
  } = useEmergencyModeStore();

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set([titleRef.current, descriptionRef.current], {
        y: 30,
        opacity: 0
      });
      
      gsap.set(alertRef.current, {
        y: 20,
        opacity: 0
      });
      
      gsap.set(formContainerRef.current, {
        y: 20,
        opacity: 0
      });
      
      gsap.set([mainCardRef.current, reportCardRef.current], {
        y: 40,
        opacity: 0
      });

      // Main entrance timeline - simplified to just appear
      const tl = gsap.timeline();
      
      // Cards entrance with stagger
      tl.to([mainCardRef.current, reportCardRef.current], {
        y: 0,
        opacity: 1,
        duration: 0.6,
        stagger: 0.1,
        ease: "power2.out"
      });

      // Header content animation
      tl.to(titleRef.current, {
        y: 0,
        opacity: 1,
        duration: 0.5,
        ease: "power2.out"
      }, "-=0.3")
      .to(descriptionRef.current, {
        y: 0,
        opacity: 1,
        duration: 0.5,
        ease: "power2.out"
      }, "-=0.2");

      // Alert fade in
      tl.to(alertRef.current, {
        y: 0,
        opacity: 1,
        duration: 0.5,
        ease: "power2.out"
      }, "-=0.2");

      // Form container fade in
      tl.to(formContainerRef.current, {
        y: 0,
        opacity: 1,
        duration: 0.5,
        ease: "power2.out"
      }, "-=0.1");

      // Remove all floating animations - elements stay in place

    }, containerRef);

    return () => ctx.revert(); // Cleanup
  }, []);

  // Simplified hover animations - just slight scale
  const handleCardHover = (cardRef: React.RefObject<HTMLDivElement>, isEntering: boolean) => {
    gsap.to(cardRef.current, {
      scale: isEntering ? 1.01 : 1,
      duration: 0.2,
      ease: "power2.out"
    });
  };

  return (
    <div ref={containerRef} className="space-y-6">
      <Card 
        ref={mainCardRef}
        className="max-w-6xl mx-auto shadow-none transition-shadow hover:shadow-lg"
        onMouseEnter={() => handleCardHover(mainCardRef, true)}
        onMouseLeave={() => handleCardHover(mainCardRef, false)}
      >
        <CardHeader className="text-center">
          <CardTitle ref={titleRef} className="text-3xl font-bold">
            {t("title")}
          </CardTitle>
          <CardDescription ref={descriptionRef} className="text-lg text-muted-foreground">
            {t("description")}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-8">
          <Alert ref={alertRef} className="transition-colors hover:bg-muted/50">
            <Lightbulb className="h-4 w-4" />
            <AlertTitle className="font-semibold">
              {t("whatToExpectTitle")}
            </AlertTitle>
            <AlertDescription>{t("whatToExpectDescription")}</AlertDescription>
          </Alert>

          <div ref={formContainerRef}>
            <EmergencyModeActivitationForm
              onSubmit={handleFormSubmit}
              isPending={isPending}
              maxHours={MAX_HOURS}
              maxDays={MAX_DAYS}
              minDays={MIN_DAYS}
            />
          </div>
        </CardContent>
      </Card>

      <Card 
        ref={reportCardRef}
        className="transition-shadow hover:shadow-lg"
        onMouseEnter={() => handleCardHover(reportCardRef, true)}
        onMouseLeave={() => handleCardHover(reportCardRef, false)}
      >
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquareWarning className="h-5 w-5 text-muted-foreground" />
            مشاركة وضعي مع الادارة
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ReportProblemForm sessionId={sessionId} />
        </CardContent>
      </Card>
    </div>
  );
}
