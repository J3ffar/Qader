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
  console.log(plans);
  const handlePurchase = (planId: string) => {
    // In a real app, this would redirect to a payment page
    // e.g., router.push(`/checkout?plan=${planId}`)
    alert(`Redirecting to purchase plan: ${planId}`);
  };

  const handleCancel = () => {
    // TODO: Implement cancel subscription mutation
    alert("Cancel subscription functionality to be implemented.");
  };

  return (
    <div className="space-y-8">
      {/* Current Subscription Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Crown className="h-6 w-6 text-yellow-500" />
            {t("current.title")}
          </CardTitle>
          <CardDescription>{t("current.description")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-1">
              <p className="font-semibold">{t("current.planName")}</p>
              <p className="text-lg font-bold">
                {currentSubscription.plan_name || t("current.noPlan")}
              </p>
            </div>
            <Badge
              variant={
                currentSubscription.is_active ? "default" : "destructive"
              }
            >
              {currentSubscription.is_active
                ? t("current.statusActive")
                : t("current.statusInactive")}
            </Badge>
          </div>
          {currentSubscription.is_active && currentSubscription.expires_at && (
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="space-y-1">
                <p className="font-semibold">{t("current.expiresAt")}</p>
                <p className="text-lg font-bold">
                  {format(new Date(currentSubscription.expires_at), "PPP", {
                    locale: dateLocale,
                  })}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancel}
                className="text-destructive hover:text-destructive"
              >
                {t("current.cancelButton")}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {!currentSubscription.is_active && <ApplySerialCodeForm />}
      <Separator />

      {/* Available Plans */}
      <div>
        <h3 className="mb-4 text-xl font-bold">{t("available.title")}</h3>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {arePlansLoading ? (
            <>
              <PlanCardSkeleton />
              <PlanCardSkeleton />
              <PlanCardSkeleton />
            </>
          ) : (
            // FIX: Use optional chaining or a fallback to ensure we map over an array.
            // (plans || []).map(...) is a safe and common pattern.
            (plans || []).map((plan) => (
              <Card key={plan.id} className="flex flex-col">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Package className="h-6 w-6 text-primary" />
                    {plan.name}
                  </CardTitle>
                  <CardDescription>
                    {t("available.duration", { days: plan.duration_days })}
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-grow">
                  <p>{plan.description}</p>
                </CardContent>
                <CardFooter>
                  <Button
                    className="w-full"
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
