"use client";

import React from "react";
import { useEmergencyModeStore } from "@/store/emergency.store";
import { EmergencyModeSetup } from "@/components/features/platform/study/emergency-mode/EmergencyModeSetup";
import { EmergencyModeSessionView } from "@/components/features/platform/study/emergency-mode/EmergencyModeSessionView";
import { EmergencyModeResults } from "@/components/features/platform/study/emergency-mode/EmergencyModeResults";
import { AnimatePresence, motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";

const pageTransition = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -20 },
  transition: { duration: 0.3 },
};

export default function EmergencyModePage() {
  const sessionStatus = useEmergencyModeStore((state) => state.sessionStatus);
  const t = useTranslations("Study.emergencyMode");

  const renderContent = () => {
    switch (sessionStatus) {
      case "active":
        return (
          <motion.div key="session" {...pageTransition}>
            <EmergencyModeSessionView />
          </motion.div>
        );
      case "completing":
        return (
          <motion.div
            key="completing"
            {...pageTransition}
            className="flex flex-col items-center justify-center min-h-[50vh] gap-4"
          >
            <Loader2 className="h-12 w-12 animate-spin text-primary" />
            <p className="text-lg font-semibold">{t("results.calculating")}</p>
            <p className="text-muted-foreground">
              {t("results.calculatingDesc")}
            </p>
          </motion.div>
        );
      case "completed":
        return (
          <motion.div key="results" {...pageTransition}>
            <EmergencyModeResults />
          </motion.div>
        );
      case "setup":
      default:
        return (
          <motion.div key="setup" {...pageTransition}>
            <EmergencyModeSetup />
          </motion.div>
        );
    }
  };

  return (
    <div className="min-h-full w-full sm:p-6">
      <AnimatePresence mode="wait">{renderContent()}</AnimatePresence>
    </div>
  );
}
