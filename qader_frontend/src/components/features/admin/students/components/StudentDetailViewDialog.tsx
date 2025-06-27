"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { getAdminUserDetail } from "@/services/api/admin/users.service";
import { queryKeys } from "@/constants/queryKeys";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { User } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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

  const { data: user, isLoading: isLoadingUser } = useQuery({
    queryKey: queryKeys.admin.userDetails.detail(userId!),
    queryFn: () => getAdminUserDetail(userId!),
    enabled: !!userId && isOpen,
  });

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="w-full h-[90vh]">
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
          ) : (
            <DialogTitle>{t("viewDetails")}</DialogTitle>
          )}
        </DialogHeader>
        <Tabs
          defaultValue="details"
          className="flex flex-col flex-grow overflow-hidden"
        >
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="details">{t("tabs.details")}</TabsTrigger>
            <TabsTrigger value="statistics">{t("tabs.statistics")}</TabsTrigger>
            <TabsTrigger value="history">{t("tabs.testHistory")}</TabsTrigger>
            <TabsTrigger value="points">{t("tabs.pointLog")}</TabsTrigger>
          </TabsList>
          <div className="flex-grow overflow-y-auto p-4">
            <TabsContent value="details">
              {userId && (
                <ProfileDetailsTab user={user} isLoading={isLoadingUser} />
              )}
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
