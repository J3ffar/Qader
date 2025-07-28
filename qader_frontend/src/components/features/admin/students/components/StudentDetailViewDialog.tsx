"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { getAdminUserDetail } from "@/services/api/admin/users.service";
import { queryKeys } from "@/constants/queryKeys";
import { cn } from "@/lib/utils";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { User } from "lucide-react";

import { ProfileDetailsTab } from "./tabs/ProfileDetailsTab";
import { StatisticsTab } from "./tabs/StatisticsTab";
import { TestHistoryTab } from "./tabs/TestHistoryTab";
import { PointLogTab } from "./tabs/PointLogTab";

interface StudentDetailViewDialogProps {
  userId: number | null;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
}

const ProfileHeader = ({
  name,
  email,
  avatarUrl,
}: {
  name: string;
  email: string;
  avatarUrl: string | null;
}) => (
  <div className="flex items-center gap-4">
    <Avatar className="h-16 w-16">
      <AvatarImage src={avatarUrl ?? undefined} alt={name} />
      <AvatarFallback>
        <User className="h-8 w-8" />
      </AvatarFallback>
    </Avatar>
    <div>
      <DialogTitle className="text-xl">{name}</DialogTitle>
      <DialogDescription>{email}</DialogDescription>
    </div>
  </div>
);

export default function StudentDetailViewDialog({
  userId,
  isOpen,
  onOpenChange,
}: StudentDetailViewDialogProps) {
  const t = useTranslations("Admin.StudentManagement");
  const [activeTab, setActiveTab] = useState("details");

  const { data: user, isLoading: isLoadingUser } = useQuery({
    queryKey: queryKeys.admin.userDetails.detail(userId!),
    queryFn: () => getAdminUserDetail(userId!),
    enabled: !!userId && isOpen,
  });

  const handleOpenChange = (open: boolean) => {
    if (open) {
      setActiveTab("details");
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent
        className={cn(
          "flex flex-col",
          "h-full sm:h-[90vh]",
          "transition-[max-width] duration-300 ease-in-out",
          activeTab === "statistics" ? "sm:max-w-7xl" : "sm:max-w-4xl"
        )}
      >
        <DialogHeader>
          {isLoadingUser ? (
            <div className="flex items-center gap-4">
              <Skeleton className="h-16 w-16 rounded-full" />
              <div className="space-y-2">
                <Skeleton className="h-6 w-40" />
                <Skeleton className="h-4 w-52" />
              </div>
            </div>
          ) : user ? (
            <ProfileHeader
              name={user.full_name}
              email={user.user.email}
              avatarUrl={user.profile_picture}
            />
          ) : null}
        </DialogHeader>

        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="w-full flex-grow overflow-hidden flex flex-col"
        >
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="details">{t("tabs.details")}</TabsTrigger>
            <TabsTrigger value="statistics">{t("tabs.statistics")}</TabsTrigger>
            <TabsTrigger value="history">{t("tabs.testHistory")}</TabsTrigger>
            <TabsTrigger value="points">{t("tabs.pointLog")}</TabsTrigger>
          </TabsList>

          <div className="flex-grow overflow-y-auto mt-4 pr-3">
            <TabsContent value="details">
              <ProfileDetailsTab user={user} isLoading={isLoadingUser} />
            </TabsContent>
            <TabsContent value="statistics">
              {userId && <StatisticsTab userId={userId} />}
            </TabsContent>
            <TabsContent value="history">
              {userId && <TestHistoryTab userId={userId} />}
            </TabsContent>
            <TabsContent value="points">
              {userId && <PointLogTab userId={userId} />}
            </TabsContent>
          </div>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
