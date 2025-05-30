"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import Image from "next/image";
import { GiftIcon as HeroGiftIcon } from "@heroicons/react/24/outline"; // Renamed to avoid conflict
import {
  Facebook,
  Linkedin,
  Youtube,
  Instagram,
  Twitter,
  Send,
  Copy,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthCore } from "@/store/auth.store";
import { getRewardStoreItems } from "@/services/gamification.service";
import { QUERY_KEYS } from "@/constants/queryKeys";
import type { RewardStoreItem } from "@/types/api/gamification.types";
import { API_BASE_URL } from "@/constants/api"; // Assuming you might want to share the platform link

const GiftContain = ({
  isVisible,
  activeSection,
  setActiveSection,
}: {
  isVisible: boolean;
  activeSection: "invite" | "store";
  setActiveSection: (section: "invite" | "store") => void;
}) => {
  const t = useTranslations("Nav.UserNav.GiftContain");
  const { user, isAuthenticated } = useAuthCore();

  const {
    data: rewardItems,
    isLoading: isLoadingRewards,
    isError: isErrorRewards,
  } = useQuery<RewardStoreItem[], Error>({
    queryKey: [QUERY_KEYS.REWARD_STORE_ITEMS],
    queryFn: getRewardStoreItems,
    enabled: isVisible && activeSection === "store" && isAuthenticated,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });

  const referralLink = useMemo(() => {
    if (user && user.referral && user.referral.code) {
      return `${
        process.env.NEXT_PUBLIC_APP_URL || "https://qader.vip"
      }/signup?ref=${user.referral.code}`;
    }
    return "";
  }, [user]);

  const copyToClipboard = () => {
    if (referralLink) {
      navigator.clipboard
        .writeText(referralLink)
        .then(() => toast.success(t("copiedSuccess")))
        .catch(() => toast.error(t("copiedError")));
    }
  };

  // Original useEffect for client-side only rendering is good
  const [isClient, setIsClient] = useState(false);
  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient || !isVisible) {
    return null;
  }

  return (
    <div className="giftcontain absolute top-1 z-50 mx-auto mt-[70px] w-full max-w-md rounded-lg border bg-popover p-5 text-popover-foreground shadow-lg ltr:right-3 rtl:left-3">
      <div className="mb-5 flex justify-between border-b border-border">
        <Button
          variant="ghost"
          onClick={() => setActiveSection("invite")}
          className={`flex-1 p-2 cursor-pointer rounded-none ${
            activeSection === "invite"
              ? "text-primary font-bold border-b-2 border-primary"
              : "text-muted-foreground"
          }`}
        >
          {t("inviteFriend.title")}
        </Button>
        <Button
          variant="ghost"
          onClick={() => setActiveSection("store")}
          className={`flex-1 p-2 cursor-pointer rounded-none ml-2 ${
            activeSection === "store"
              ? "text-primary font-bold border-b-2 border-primary"
              : "text-muted-foreground"
          }`}
        >
          {t("store.title")}
        </Button>
      </div>

      {activeSection === "invite" && (
        <div>
          <p className="mb-1 text-lg font-semibold">
            {t("inviteFriend.header")}
          </p>
          <p className="mb-5 text-sm text-muted-foreground">
            {t("inviteFriend.description")}
          </p>
          <div className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-muted/50 p-5 sm:flex-row sm:gap-5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/20">
              <HeroGiftIcon className="h-6 w-6 font-bold text-primary" />
            </span>
            <div className="flex-1 text-center sm:text-right">
              <span className="text-xs text-muted-foreground">
                {t("inviteFriend.referralLink")}
              </span>
              {isAuthenticated && !user ? (
                <Skeleton className="mt-1 h-5 w-full sm:w-3/4" />
              ) : user?.referral?.code ? (
                <div className="mt-1 flex items-center gap-2">
                  <a
                    href={referralLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="break-all text-sm text-foreground underline"
                  >
                    {referralLink}
                  </a>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={copyToClipboard}
                    className="h-7 w-7"
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              ) : (
                <p className="mt-1 text-sm text-muted-foreground">
                  {t("inviteFriend.noCode")}
                </p>
              )}
            </div>
          </div>
          {/* Social Share Icons - these typically share a generic platform link or the referral link */}
          <div className="mt-5 flex items-center justify-center gap-3">
            {[Facebook, Linkedin, Youtube, Instagram, Twitter, Send].map(
              (Icon, idx) => (
                <Button
                  key={idx}
                  variant="outline"
                  size="icon"
                  className="h-8 w-8 rounded-full"
                  onClick={() => {
                    // Implement social sharing logic here, e.g., window.open(...)
                    // For now, just a placeholder
                    const shareUrl =
                      referralLink ||
                      process.env.NEXT_PUBLIC_APP_URL ||
                      "https://qader.vip";
                    toast.info(
                      `Sharing ${Icon.displayName || "link"}: ${shareUrl}`
                    );
                  }}
                >
                  <Icon className="h-4 w-4" />
                </Button>
              )
            )}
          </div>
        </div>
      )}

      {activeSection === "store" && (
        <div>
          {isLoadingRewards && (
            <>
              <Skeleton className="mb-1 h-6 w-3/4" />
              <Skeleton className="mb-5 h-4 w-full" />
              <Skeleton className="h-32 w-full rounded-2xl" />
            </>
          )}
          {isErrorRewards && (
            <p className="py-10 text-center text-destructive">
              {t("store.errorLoading")}
            </p>
          )}
          {!isLoadingRewards && !isErrorRewards && (
            <>
              {rewardItems && rewardItems.length > 0 ? (
                <>
                  <p className="mb-1 text-lg font-semibold">
                    {t("store.hasOffersHeader")}
                  </p>
                  <p className="mb-5 text-sm text-muted-foreground">
                    {t("store.hasOffersDescription")}
                  </p>
                  {/* Simple display of first item, can be more complex */}
                  <div className="flex flex-col items-center gap-2 rounded-2xl border border-border bg-muted/50 p-5">
                    {rewardItems[0].image_url && (
                      <Image
                        src={rewardItems[0].image_url}
                        width={60}
                        height={60}
                        alt={rewardItems[0].name}
                        className="rounded-md"
                      />
                    )}
                    <p className="font-bold">{rewardItems[0].name}</p>
                    <p className="text-center text-sm text-muted-foreground">
                      {rewardItems[0].description}
                    </p>
                    <p className="font-semibold text-primary">
                      {t("store.pointsCost", {
                        count: rewardItems[0].cost_points,
                      })}
                    </p>
                    <Button size="sm" className="mt-2">
                      {t("store.redeemButton")}
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <p className="mb-1 text-lg font-semibold">
                    {t("store.noOffersHeader")}
                  </p>
                  <p className="mb-5 text-sm text-muted-foreground">
                    {t("store.noOffersDescription")}
                  </p>
                  <div className="flex flex-col items-center gap-1 rounded-2xl border border-border bg-muted/50 p-7">
                    <Image
                      src="/images/gift.png"
                      width={50}
                      height={50}
                      alt={t("store.giftAlt")}
                    />
                    <p className="font-bold">{t("store.noSpecialOffers")}</p>
                    <p className="text-center text-sm text-muted-foreground">
                      {t("store.willBeNotified")}
                    </p>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default GiftContain;
