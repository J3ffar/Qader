"use client";

import { motion } from "framer-motion";
import { useTranslations } from "next-intl";
// import { QaderLogo } from ".//QaderLogo"; // Assuming you have a logo component

export function FullScreenLoader() {
  // Use the translations hook to get the "Common" namespace
  const t = useTranslations("Common");

  // Animation variants for the container of the bars
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15, // Delay between each child's animation
        delayChildren: 0.2,
      },
    },
  };

  // Animation variants for each individual bar
  const barVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5,
        ease: "easeInOut",
        repeat: Infinity,
        repeatType: "mirror" as const, // Makes the animation reverse
      },
    },
  };

  return (
    <div className="fixed inset-0 z-[100] flex flex-col items-center justify-center bg-background/80 backdrop-blur-sm">
      <div className="flex flex-col items-center justify-center space-y-6">
        {/* You can add your logo here for better branding */}
        {/* <QaderLogo className="h-12 w-auto text-primary" /> */}

        {/* The animated loader */}
        <motion.div
          className="flex h-10 items-end justify-center space-x-2 "
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          aria-label={t("loading")} // Accessibility
        >
          {/* Create 3 animated bars */}
          <motion.div
            className="h-6 w-2 rounded-full bg-primary"
            variants={barVariants}
          />
          <motion.div
            className="h-10 w-2 rounded-full bg-primary"
            variants={barVariants}
            style={{ animationDelay: "0.2s" }} // Manual delay to offset animations
          />
          <motion.div
            className="h-6 w-2 rounded-full bg-primary"
            variants={barVariants}
            style={{ animationDelay: "0.4s" }}
          />
        </motion.div>

        {/* The text in Arabic */}
        <p className="text-lg font-medium text-foreground/80 tracking-wide">
          {t("loading")}...
        </p>
      </div>
    </div>
  );
}
