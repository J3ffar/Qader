"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useAuthStore } from "@/store/auth.store";
import { getCurrentUserProfile } from "@/services/auth.service";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Terminal } from "lucide-react";

import AccountSettingsForm from "./_components/AccountSettingsForm";
import NotificationsSettingsForm from "./_components/NotificationsSettingsForm";
import SubscriptionDetails from "./_components/SubscriptionDetails";
import SettingsPageSkeleton from "./_components/SettingsPageSkeleton";
import { getSubscriptionPlans } from "@/services/subscription.service";
import { queryKeys } from "@/constants/queryKeys";
import { UserProfile } from "@/types/api/auth.types";
import { useParams } from "next/navigation";

// Assume this service function exists to fetch plans
// In a real scenario, this would be in `learning.service.ts` or a `subscription.service.ts`
// const getSubscriptionPlans = () => apiClient<Plan[]>('/users/subscription-plans/');

export default function SettingsPage() {
  const t = useTranslations("Study.settings");
  const userFromStore = useAuthStore((state) => state.user);
  const {locale} = useParams<{ locale: "ar" | "en" }>();
  

  // Fetch current user profile data
  const {
    data: userProfile,
    isLoading: isUserLoading,
    error: userError,
  } = useQuery({
    queryKey: queryKeys.user.profile(
      userFromStore ? (userFromStore as UserProfile).id : null
    ),
    queryFn: getCurrentUserProfile,
    initialData: userFromStore, // Use Zustand data for initial render, prevents flicker
    enabled: !!userFromStore?.id,
  });

  const {
    data: plans,
    isLoading: arePlansLoading,
    error: plansError,
  } = useQuery({
    queryKey: queryKeys.user.subscription(),
    queryFn: getSubscriptionPlans,
  });

  if ((isUserLoading && !userProfile) || (arePlansLoading && !plans)) {
    return <SettingsPageSkeleton />;
  }

  if (userError) {
    return (
      <Alert variant="destructive">
        <Terminal className="h-4 w-4" />
        <AlertTitle>{t("error.title")}</AlertTitle>
        <AlertDescription>{t("error.message")}</AlertDescription>
      </Alert>
    );
  }

  if (!userProfile) {
    // This case handles when user is logged out or data is missing
    return null;
  }

  if (plansError) {
    console.error("Failed to fetch subscription plans:", plansError);
    // Optionally render an inline error message for the plans section
  }

  return (
    <div className="space-y-6">
      <header>
        <h2 className="text-2xl font-bold tracking-tight">{t("title")}</h2>
        <p className="text-muted-foreground">{t("description")}</p>
      </header>
      <Separator />

      <Tabs defaultValue="account" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="account">{t("tabs.account")}</TabsTrigger>
          <TabsTrigger value="subscriptions">
            {t("tabs.subscriptions")}
          </TabsTrigger>
          <TabsTrigger value="notifications">
            {t("tabs.notifications")}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="account">
          <AccountSettingsForm user={userProfile} />
        </TabsContent>

        <TabsContent value="subscriptions">
          <SubscriptionDetails
            currentSubscription={userProfile.subscription}
            plans={plans || []}
            arePlansLoading={arePlansLoading}
            locale={locale}
          />
        </TabsContent>

        <TabsContent value="notifications">
          <NotificationsSettingsForm user={userProfile} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
