"use client";

import { useTranslations } from "next-intl";
import { CheckCircle2, Crown, Package, XCircle } from "lucide-react";
import { format } from "date-fns";
import { arSA, enUS } from "date-fns/locale";

import type { SubscriptionPlan } from "@/types/api/subscription.types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import { SubscriptionDetailResponse } from "@/types/api/auth.types";
import ApplySerialCodeForm from "./ApplySerialCodeForm";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth.store";
import { cancelSubscription } from "@/services/subscription.service";
import { toast } from "sonner";
import { UserProfile } from "@/types/api/user.types";
import { getApiErrorMessage } from "@/utils/getApiErrorMessage";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { queryKeys } from "@/constants/queryKeys";
import { cn } from "@/lib/utils";

interface SubscriptionDetailsProps {
  currentSubscription: SubscriptionDetailResponse;
  plans: SubscriptionPlan[];
  arePlansLoading: boolean;
  locale: "ar" | "en";
}

const PlanCardSkeleton = () => (
  <Card>
    <CardHeader>
      <Skeleton className="h-6 w-32" />
      <Skeleton className="h-4 w-48" />
    </CardHeader>
    <CardContent className="space-y-2">
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
    </CardContent>
    <CardFooter>
      <Skeleton className="h-10 w-full" />
    </CardFooter>
  </Card>
);


export default function SubscriptionDetails({
  currentSubscription,
  plans,
  arePlansLoading,
  locale,
}: SubscriptionDetailsProps) {
  const t = useTranslations("Study.settings.subscriptions");
  const dateLocale = locale === "ar" ? arSA : enUS;
  const queryClient = useQueryClient();
  const { user, updateUserProfile: updateUserInStore } = useAuthStore();

  const handlePurchase = (planId: string) => {
    // In a real app, this would redirect to a payment page
    // e.g., router.push(`/checkout?plan=${planId}`)
    alert(`Redirecting to purchase plan: ${planId}`);
  };

  const cancelMutation = useMutation({
    mutationFn: cancelSubscription,
    onSuccess: (data) => {
      toast.success(t("cancelDialog.toast.successTitle"), {
        description: data.detail,
      });

      // Instantly update user profile in both caches
      queryClient.setQueryData<UserProfile>(
        queryKeys.user.profile((user as UserProfile).id),
        (oldData) =>
          oldData ? { ...oldData, subscription: data.subscription } : undefined
      );
      updateUserInStore({ subscription: data.subscription });
    },
    onError: (error) => {
      toast.error(t("cancelDialog.toast.errorTitle"), {
        description: getApiErrorMessage(
          error,
          t("cancelDialog.toast.errorTitle")
        ),
      });
    },
  });

  return (
    <div className="flex space-y-8 max-w-7xl justify-center items-center flex-col mx-auto mt-8">
      {/* Current Subscription Card */}
      <Card className="overflow-hidden w-full border-2 dark:bg-[#0B1739] dark:border-[#7E89AC]">
        <CardHeader dir={locale==="en"?"ltr":"rtl"} className="flex flex-col">
          <CardTitle dir={locale==="en"?"ltr":"rtl"} className="flex items-center gap-2">
            <Crown className="h-6 w-6 text-yellow-500" />
            <span>{t("current.title")}</span>
          </CardTitle>
          <CardDescription className={locale === "ar" ? "text-right" : "text-left"}>{t("current.description")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 flex flex-col items-center">
          <div dir={locale ==="en"?"ltr":"rtl"} className="flex items-center justify-between rounded-lg border p-4 w-full">
            <div>
              <p className="font-semibold">{t("current.planName")}</p>
              <p className="text-lg font-bold">
                {currentSubscription.plan_name || t("current.noPlan")}
              </p>
            </div>
            <Badge
              variant={
                currentSubscription.is_active ? "default" : "destructive"
              }
              className="flex items-center text-center w-24 h-7 justify-center text-md"
            >
              {currentSubscription.is_active
                ? t("current.statusActive")
                : t("current.statusInactive")}
            </Badge>
          </div>
         {currentSubscription.is_active && currentSubscription.expires_at && ( 
            <div dir={locale ==="en"?"ltr":"rtl"} className="flex justify-between items-center rounded-lg border p-4 w-full">
              <div>
                <p className= "font-semibold">{t("current.expiresAt")}</p>
                <p className="text-lg font-bold">
                  {/* {format(new Date(currentSubscription.expires_at), "PPP", {
                    locale: dateLocale,
                  })} */}
                </p>
              </div>

              {/* FIX: Integrate AlertDialog for cancellation */}
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="cursor-pointer text-destructive hover:text-destructive dar:border-2 hover:border-destructive/90 dark:border-[#7E89AC]"
                  >
                    {t("current.cancelButton")}
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent  className="flex flex-col">
                  <AlertDialogHeader dir={locale ==="en"?"ltr":"rtl"}>
                    <AlertDialogTitle className={locale === "ar" ? "text-right" : "text-left"}>
                      {t("cancelDialog.title")}
                    </AlertDialogTitle>
                    <AlertDialogDescription className={locale === "ar" ? "text-right" : "text-left"}>
                      {t("cancelDialog.description")}
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel className="cursor-pointer">
                      {t("cancelDialog.cancelButton")}
                    </AlertDialogCancel>
                    <AlertDialogAction
                      onClick={() => cancelMutation.mutate()}
                      disabled={cancelMutation.isPending}
                      className="bg-destructive text-destructive-foreground text-white hover:bg-destructive/90 cursor-pointer"
                    >
                      {cancelMutation.isPending
                        ? t("cancelDialog.confirmButtonLoading")
                        : t("cancelDialog.confirmButton")}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          )} 
        </CardContent>
      </Card>

      {!currentSubscription.is_active && <ApplySerialCodeForm />}
      <Separator />

      {/* Available Plans */}
      <div className="space-y-4 flex flex-col w-full">
        <h3 dir={locale ==="en"?"ltr":"rtl"} className="mb-4 text-xl font-bold">{t("available.title")}</h3>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2 lg:grid-cols-3 w-11/12 mx-auto">
          {arePlansLoading ? (
            <>
              <PlanCardSkeleton />
              <PlanCardSkeleton />
              <PlanCardSkeleton />
            </>
          ) : (
            // FIX: Use optional chaining or a fallback to ensure we map over an array.
            // (plans || []).map(...) is a safe and common pattern.
            (plans || []).map((plan, index) => (
              <Card key={plan.id} className={`flex flex-col transition-all duration-300 ease-in-out transform hover:scale-105 hover:translate-y-[-10px] ${
              index === 1 ? "shadow-lg dark:hover:bg-[#074182] dark:bg-[#0B1739] dark:border-[#7E89AC]" : " dark:border-[#7E89AC] dark:hover:bg-[#074182] dark:bg-[#0B1739] z-10 hover:shadow-xl rounded-lg p-4"}`}>
                <CardHeader dir={locale ==="en"?"ltr":"rtl"}>
                  <CardTitle className="flex items-center gap-2">
                    <Package className="h-6 w-6 text-primary" />
                    {plan.name}
                  </CardTitle>
                  <CardDescription className="text-sm text-gray-400">

                    {t("available.duration", { days: plan.duration_days })}
                  </CardDescription>
                </CardHeader>
                <CardContent dir={locale ==="en"?"ltr":"rtl"} className="flex-grow">
                  <p className="text-gray-300 mt-4">{plan.description}</p>
                </CardContent>
                <CardFooter>
                  <Button
                    className="w-full mt-4 cursor-pointer"
                    onClick={() => handlePurchase(plan.id)}
                  >
                    {t("available.purchaseButton")}
                  </Button>
                </CardFooter>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
