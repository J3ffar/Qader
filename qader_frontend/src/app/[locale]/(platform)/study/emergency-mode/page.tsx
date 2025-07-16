"use client";

import React from "react";
import { useEmergencyModeStore } from "@/store/emergency.store";
import { EmergencyModeSetup } from "@/components/features/platform/study/emergency-mode/EmergencyModeSetup";
import { EmergencyModeSessionView } from "@/components/features/platform/study/emergency-mode/EmergencyModeSessionView";
import { AnimatePresence, motion } from "framer-motion";

export default function EmergencyModePage() {
  const isSessionActive = useEmergencyModeStore(
    (state) => state.isSessionActive
  );

  return (
    <div className="min-h-full w-full dark:bg-gray-900 sm:p-6">
      <AnimatePresence mode="wait">
        {!isSessionActive ? (
          <motion.div
            key="setup"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <EmergencyModeSetup />
          </motion.div>
        ) : (
          <motion.div
            key="session"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <EmergencyModeSessionView />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
