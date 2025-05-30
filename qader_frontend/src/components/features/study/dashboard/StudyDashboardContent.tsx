import React from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { QuickStats } from "./QuickStats";
import { QuickActionsGrid } from "./QuickActionsGrid";
import { UserProfile } from "@/types/api/auth.types";
import Image from "next/image";
import { useTranslations } from "next-intl";
import { User } from "lucide-react"; // Fallback icon

interface StudyDashboardContentProps {
  user: UserProfile;
}

export const StudyDashboardContent: React.FC<StudyDashboardContentProps> = ({
  user,
}) => {
  const t = useTranslations("Study.StudyPage.dashboard");
  const userName = user.preferred_name || user.full_name;

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="flex items-center space-x-4">
        {/* <Avatar className="h-16 w-16">
          {user.profile_picture_url ? (
            <Image
              src={user.profile_picture_url}
              alt={userName || "User Avatar"}
              width={64}
              height={64}
              className="rounded-full object-cover"
            />
          ) : (
            <AvatarFallback>
              <User className="h-8 w-8" />
            </AvatarFallback>
          )}
        </Avatar> */}
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {t("welcomeMessage", { name: userName })}
          </h1>
          <p className="text-muted-foreground">{t("welcomeSubMessage")}</p>
        </div>
      </div>

      {/* Quick Stats */}
      <QuickStats
        points={user.points ?? 0}
        currentStreakDays={user.current_streak_days ?? 0}
      />

      {/* Quick Actions Grid */}
      <QuickActionsGrid user={user} />

      {/* Placeholder for future sections like "Recommended for you" or "Recent Activity" */}
    </div>
  );
};
