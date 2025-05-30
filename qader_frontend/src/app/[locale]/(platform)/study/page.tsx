"use client"; // This page interacts with client-side auth state and has user-specific conditional rendering

import React, { useEffect, useState } from "react";
import { useAuthCore } from "@/store/auth.store";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PATHS } from "@/constants/paths";
import { ActionPromptCard } from "@/components/features/study/dashboard/ActionPromptCard";
import { StudyDashboardContent } from "@/components/features/study/dashboard/StudyDashboardContent";
import { ClipboardEdit, Target, AlertTriangle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const StudyPage = () => {
  const tS = useTranslations("Study.StudyPage");
  const tC = useTranslations("Common");
  const { user, isAuthenticated, isProfileComplete } = useAuthCore();
  const router = useRouter();

  // Zustand persistence might take a moment to rehydrate.
  // We add a local loading state to prevent flicker or showing content prematurely.
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // If isAuthenticated is determined (true or false) and user object is accordingly set (or null if not auth),
    // then we can stop loading. This handles initial load and rehydration.
    if (isAuthenticated !== undefined) {
      // Check if isAuthenticated has been resolved
      setIsLoading(false);
    }
  }, [isAuthenticated, user]);

  // Handle redirection if not authenticated (middleware should also cover this)
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(PATHS.LOGIN);
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || (isAuthenticated && !user)) {
    // Show skeletons while loading user data or if auth check is in progress
    return (
      <div className="space-y-8 p-4 md:p-6">
        <div className="flex items-center space-x-4">
          <Skeleton className="h-16 w-16 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  // If authenticated but user data is somehow still null (should not happen if store logic is correct)
  // Or if not authenticated (though middleware should redirect)
  if (!user) {
    // This case should ideally be handled by redirection or a more specific error message
    // if isAuthenticated is true but user is null after loading.
    return (
      <div className="flex min-h-[calc(100vh-200px)] flex-col items-center justify-center text-center">
        <AlertTriangle className="mb-4 h-16 w-16 text-destructive" />
        <h2 className="mb-2 text-2xl font-semibold">
          {tS("errorLoadingUserTitle")}
        </h2>
        <p className="mb-6 text-muted-foreground">
          {tS("errorLoadingUserMessage")}
        </p>
        <Button asChild>
          <Link href={PATHS.LOGIN}>{tC("login")}</Link>
        </Button>
      </div>
    );
  }

  if (!isProfileComplete) {
    return (
      <div className="flex min-h-[calc(100vh-200px)] items-center justify-center p-4">
        <ActionPromptCard
          title={tS("completeProfile.title")}
          description={tS("completeProfile.description")}
          buttonText={tS("completeProfile.button")}
          buttonHref={PATHS.COMPLETE_PROFILE}
          icon={ClipboardEdit}
        />
      </div>
    );
  }

  if (!user.level_determined) {
    return (
      <div className="flex min-h-[calc(100vh-200px)] items-center justify-center p-4">
        <ActionPromptCard
          title={tS("determineLevel.title")}
          description={tS("determineLevel.description")}
          buttonText={tS("determineLevel.button")}
          buttonHref={`${PATHS.STUDY_HOME}/determine-level`}
          icon={Target}
        />
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6">
      <StudyDashboardContent user={user} />
    </div>
  );
};

export default StudyPage;
