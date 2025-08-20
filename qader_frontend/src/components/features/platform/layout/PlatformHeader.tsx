"use client";

import { useState, useRef, forwardRef, useEffect } from "react"; // Added forwardRef
import Image from "next/image";
import { useTranslations } from "next-intl";
import {
  MagnifyingGlassIcon,
  StarIcon,
  GiftIcon,
  BellIcon,
  ChevronDownIcon,
} from "@heroicons/react/24/outline"; // Assuming Heroicons are still desired, Lucide could be an alternative
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthCore } from "@/store/auth.store"; // Path might change based on final store location
import { cn } from "@/lib/utils"; // Path likely fine
import { useOnClickOutside } from "@/hooks/useOnClickOutside";

// Updated import paths for dropdown components
import PointsSummaryDropdown from "./platform-header/PointsSummaryDropdown";
import StreakDropdown from "./platform-header/StreakDropdown";
import GiftDropdown from "./platform-header/GiftDropdown";
import NotificationsDropdown from "./platform-header/NotificationsDropdown";
import UserProfileDropdown from "./platform-header/UserProfileDropdown";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import Link from "next/link";

interface PlatformHeaderProps {
  isSidebarOpen: boolean; // Renamed from isOpen for clarity if it refers to a sidebar
}

type DropdownId =
  | "streak"
  | "points"
  | "gift"
  | "notifications"
  | "userProfile"
  | null; // Renamed for clarity

// forwardRef is used if this component needs to be a ref target itself.
// If not, it can be removed. For now, assuming it might be useful.
const PlatformHeader = forwardRef<HTMLDivElement, PlatformHeaderProps>(
  ({ isSidebarOpen }, ref) => {
    const tNav = useTranslations("Nav.PlatformHeader"); // Assuming i18n keys remain similar
    const { user, isAuthenticated } = useAuthCore();
    const [isClientReady, setIsClientReady] = useState(false);

    const [activeDropdownId, setActiveDropdownId] = useState<DropdownId>(null);
    const [giftActiveSection, setGiftActiveSection] = useState<
      "invite" | "store"
    >("invite");

    // Refs for triggers
    const streakTriggerRef = useRef<HTMLSpanElement>(null);
    const pointsTriggerRef = useRef<HTMLSpanElement>(null);
    const giftTriggerRef = useRef<HTMLSpanElement>(null);
    const notificationsTriggerRef = useRef<HTMLSpanElement>(null);
    const userProfileTriggerRef = useRef<HTMLDivElement>(null);

    // Refs for dropdowns
    const streakDropdownRef = useRef<HTMLDivElement>(null);
    const pointsDropdownRef = useRef<HTMLDivElement>(null);
    const giftDropdownRef = useRef<HTMLDivElement>(null);
    const notificationsDropdownRef = useRef<HTMLDivElement>(null);
    const userProfileDropdownRef = useRef<HTMLDivElement>(null);

    const handleToggleDropdown = (id: NonNullable<DropdownId>) => {
      setActiveDropdownId((prevId) => (prevId === id ? null : id));
    };

    const closeAllDropdowns = () => {
      setActiveDropdownId(null);
    };

    useOnClickOutside(
      streakDropdownRef,
      streakTriggerRef,
      closeAllDropdowns,
      activeDropdownId === "streak"
    );
    useOnClickOutside(
      pointsDropdownRef,
      pointsTriggerRef,
      closeAllDropdowns,
      activeDropdownId === "points"
    );
    useOnClickOutside(
      giftDropdownRef,
      giftTriggerRef,
      closeAllDropdowns,
      activeDropdownId === "gift"
    );
    useOnClickOutside(
      notificationsDropdownRef,
      notificationsTriggerRef,
      closeAllDropdowns,
      activeDropdownId === "notifications"
    );
    useOnClickOutside(
      userProfileDropdownRef,
      userProfileTriggerRef,
      closeAllDropdowns,
      activeDropdownId === "userProfile"
    );

    const getInitials = (name: string | undefined | null): string => {
      if (!name) return "Q";
      return name
        .split(" ")
        .map((n) => n[0])
        .slice(0, 2)
        .join("")
        .toUpperCase();
    };

    // Style might need adjustment based on actual sidebar implementation details
    // This needs to be robust and consider the overall layout structure.
    const navbarStyle = {
      // Example: Assuming sidebar width is passed or from CSS variables
      // left: isSidebarOpen ? "var(--sidebar-width-open)" : "var(--sidebar-width-closed)",
      // right: "0px",
      // For simplicity, if it's dynamically positioned from the parent, these might not be needed here.
      // The positioning with 'right: 110px/50px' and 'left: 0px' seems unusual
      // and suggests it overlays the sidebar, which might be complex.
      // A more common pattern: parent layout defines regions, header fills its designated region.
      // If the values like 110px and 50px are fixed, they could be Tailwind arbitrary values or CSS vars.
    };

    useEffect(() => {
      setIsClientReady(true);
    }, []);

    if (!isClientReady) {
      // Render a minimal loader or the skeleton if it's safe for SSR mismatch
      // For a full header, usually better to wait for client readiness to avoid flash
      return <PlatformHeaderSkeleton />;
    }

    return (
      <div
        ref={ref} // Apply the forwarded ref here
        className="sticky top-0 z-40 flex h-auto dark:bg-[#091029] flex-col border-b-[0.5px] border-border bg-background px-5 shadow-sm transition-all duration-300 dark:border-gray-700 max-md:py-3"
        // style={navbarStyle} // Re-evaluate this styling approach
      >
        <div className="flex flex-col-reverse items-center justify-around gap-6 p-4 lg:h-[70px] lg:flex-row lg:gap-0">
          {/* Search Bar */}
          <div className=" bg-primary px-4 py-2 text-white">
            <Link href="/">العودة إلى الصفحة الرئيسية</Link>
          </div>

          {/* Icons: Points, Streak, Gift */}
          <div className="max-sm:hidden flex items-center gap-4 mx-2">
             <ThemeToggle />
            {/* Streak (Stars) */}
            <span
              ref={streakTriggerRef}
              className={cn(
                "flex items-center gap-1 cursor-pointer rounded-xl p-2 border",
                activeDropdownId === "streak"
                  ? "bg-muted dark:bg-muted/50"
                  : "hover:bg-muted dark:hover:bg-muted/50"
              )}
              onClick={() => handleToggleDropdown("streak")}
              role="button" // Accessibility: indicate it's interactive
              tabIndex={0} // Accessibility: make it focusable
              onKeyDown={(e) =>
                e.key === "Enter" && handleToggleDropdown("streak")
              } // Accessibility: keyboard activation
            >
              <StarIcon className="h-6 w-6 text-yellow-500" />
              {isAuthenticated && !user ? (
                <Skeleton className="h-4 w-6" />
              ) : (
                user?.current_streak_days ?? 0
              )}
            </span>

            {/* Points (Gems) */}
            <span
              ref={pointsTriggerRef}
              className={cn(
                "flex items-center gap-1 min-w-fit cursor-pointer rounded-xl p-2 border",
                activeDropdownId === "points"
                  ? "bg-muted dark:bg-muted/50"
                  : "hover:bg-muted dark:hover:bg-muted/50"
              )}
              onClick={() => handleToggleDropdown("points")}
              role="button"
              tabIndex={0}
              onKeyDown={(e) =>
                e.key === "Enter" && handleToggleDropdown("points")
              }
            >
              <Image
                src="/images/hexagon.png" // Ensure this path is correct from `public/`
                width={25}
                height={25}
                alt="gems" // Should be localized if "gems" is UI text
              />
              {isAuthenticated && !user ? (
                <Skeleton className="h-4 w-8" />
              ) : (
                user?.points ?? 0
              )}
            </span>

            {/* Gift */}
            <span
              ref={giftTriggerRef}
              className={cn(
                "relative cursor-pointer rounded-xl p-2 border",
                activeDropdownId === "gift"
                  ? "bg-muted dark:bg-muted/50"
                  : "hover:bg-muted dark:hover:bg-muted/50"
              )}
              onClick={() => handleToggleDropdown("gift")}
              role="button"
              tabIndex={0}
              onKeyDown={(e) =>
                e.key === "Enter" && handleToggleDropdown("gift")
              }
            >
              <GiftIcon className="h-6 w-6 text-pink-500" />
              <span className="absolute right-1 top-1 h-3 w-3 rounded-full border-2 border-background bg-red-500"></span>
            </span>
          </div>

          {/* Notifications and User Profile */}
          <div className="flex items-center gap-4 sm:border-r dark:border-white h-8 mx-2">
            {/* Bell Icon / Notifications */}
            <span
              ref={notificationsTriggerRef}
              className={cn(
                "relative cursor-pointer rounded-xl p-2 rtl:mr-4 ltr:ml-4 border",
                activeDropdownId === "notifications"
                  ? "bg-muted dark:bg-muted/50"
                  : "hover:bg-muted dark:hover:bg-muted/50"
              )}
              onClick={() => handleToggleDropdown("notifications")}
              role="button"
              tabIndex={0}
              onKeyDown={(e) =>
                e.key === "Enter" && handleToggleDropdown("notifications")
              }
            >
              <BellIcon className="h-6 w-6" />
              {isAuthenticated &&
                user &&
                user.unread_notifications_count > 0 && (
                  <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                    {user.unread_notifications_count > 9
                      ? "9+"
                      : user.unread_notifications_count}
                  </span>
                )}
              {isAuthenticated && !user && (
                <Skeleton className="absolute -right-1 -top-1 h-5 w-5 rounded-full" />
              )}
            </span>

            {/* User Avatar and Name */}
            <div
              ref={userProfileTriggerRef}
              onClick={() => handleToggleDropdown("userProfile")}
              className={cn(
                "relative flex items-center gap-2 cursor-pointer rounded-xl p-2 border",
                activeDropdownId === "userProfile"
                  ? "bg-muted dark:bg-muted/50"
                  : "hover:bg-muted dark:hover:bg-muted/50"
              )}
              role="button"
              tabIndex={0}
              onKeyDown={(e) =>
                e.key === "Enter" && handleToggleDropdown("userProfile")
              }
            >
              {isAuthenticated && !user ? (
                <Skeleton className="h-10 w-10 rounded-full" />
              ) : user ? (
                <Avatar className="h-10 w-10">
                  <AvatarImage
                    src={user.profile_picture_url || undefined}
                    alt={
                      user.full_name ||
                      user.username ||
                      tNav("userAvatarAltFallback")
                    }
                  />
                  <AvatarFallback>
                    {getInitials(user.full_name || user.username)}
                  </AvatarFallback>
                </Avatar>
              ) : (
                // Placeholder for non-authenticated state if header is shown (unlikely for this component)
                <div className="h-10 w-10 rounded-full bg-muted" />
              )}
              {isAuthenticated &&
                user && ( // Online status indicator
                  <span className="absolute top-1 h-3 w-3 rounded-full border-2 border-background bg-green-500 ltr:left-1 rtl:right-1"></span>
                )}
              {isAuthenticated && !user ? (
                <div className="hidden flex-col items-end space-y-1 md:flex">
                  <Skeleton className="h-4 w-[100px]" />
                  <Skeleton className="h-3 w-[70px]" />
                </div>
              ) : user ? (
                <div className="flex-col items-end md:flex">
                  <p className="text-sm font-medium">
                    {user.preferred_name || user.full_name || user.username}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {tNav("greeting")}{" "}
                    {/* Make sure "greeting" is a valid key */}
                  </p>
                </div>
              ) : null}
              <ChevronDownIcon className="h-5 w-5 text-muted-foreground" />
            </div>
          </div>
        </div>

        {/* Dropdowns Area */}
        {/* The `ref` prop on a simple div might not be what useOnClickOutside needs if the dropdown itself handles its own root element with a ref. */}
        {/* Ensure child components correctly forward refs if they are functional components. */}
        <div ref={streakDropdownRef}>
          {" "}
          {/* This div might be redundant if StreakDropdown handles its own ref and visibility */}
          <StreakDropdown isVisible={activeDropdownId === "streak"} />
        </div>
        <div ref={pointsDropdownRef}>
          <PointsSummaryDropdown isVisible={activeDropdownId === "points"} />
        </div>
        <div ref={giftDropdownRef}>
          <GiftDropdown
            isVisible={activeDropdownId === "gift"}
            activeSection={giftActiveSection}
            setActiveSection={setGiftActiveSection}
          />
        </div>
        <div ref={notificationsDropdownRef}>
          <NotificationsDropdown
            isVisible={activeDropdownId === "notifications"}
          />
        </div>
        <div ref={userProfileDropdownRef}>
          <UserProfileDropdown isVisible={activeDropdownId === "userProfile"} />
        </div>
      </div>
    );
  }
);

PlatformHeader.displayName = "PlatformHeader"; // Good practice for HOCs or forwardRef

const PlatformHeaderSkeleton = () => {
  return (
    <div
      className="sticky top-0 z-40 flex h-auto flex-col border-b-[0.5px] border-border bg-background px-5 shadow-sm transition-all duration-300 dark:border-gray-700 max-md:py-3"
      aria-hidden="true" // Indicate to assistive technologies that this is a placeholder
    >
      <div className="flex flex-col-reverse items-center justify-between gap-6 p-4 lg:h-[70px] lg:flex-row lg:gap-0">
        {/* Search Bar Skeleton */}
        <div className="flex w-full flex-1 items-center justify-start lg:w-auto">
          <div className="flex w-full max-w-md items-center overflow-hidden rounded-lg border bg-card dark:bg-transparent">
            <MagnifyingGlassIcon className="h-5 w-5 text-muted-foreground ltr:ml-2 rtl:mr-2" />
            {/* Skeleton for the input field */}
            <Skeleton className="h-10 flex-1 bg-transparent p-2" />
          </div>
          {/* Skeleton for the search button */}
          <Skeleton className="h-10 w-10 rounded-lg ltr:ml-2 rtl:mr-2" />
        </div>

        {/* Icons: Points, Streak, Gift Skeletons */}
        <div className="flex items-center gap-4">
          {/* Streak (Stars) Skeleton */}
          <span
            className={cn(
              "flex items-center gap-1 cursor-default rounded-xl p-2 border"
            )}
          >
            <StarIcon className="h-6 w-6 text-yellow-500" />
            <Skeleton className="h-4 w-6" />
          </span>

          {/* Points (Gems) Skeleton */}
          <span
            className={cn(
              "flex items-center gap-1 cursor-default rounded-xl p-2 border"
            )}
          >
            <Image
              src="/images/hexagon.png" // Ensure this path is correct from `public/`
              width={25}
              height={25}
              alt="Gems icon" // Generic alt for skeleton
            />
            <Skeleton className="h-4 w-8" />
          </span>

          {/* Gift Skeleton */}
          <span className={cn("relative cursor-default rounded-xl p-2 border")}>
            <GiftIcon className="h-6 w-6 text-pink-500" />
            {/* Skeleton for the notification dot */}
            <Skeleton className="absolute right-1 top-1 h-3 w-3 rounded-full border-2 border-background" />
          </span>
        </div>

        {/* Notifications and User Profile Skeletons */}
        <div className="flex items-center gap-4">
          {/* Bell Icon / Notifications Skeleton */}
          <span
            className={cn(
              "relative cursor-default rounded-xl p-2 rtl:mr-4 ltr:ml-4 border"
            )}
          >
            <BellIcon className="h-6 w-6" />
            {/* Skeleton for the notification count badge */}
            <Skeleton className="absolute -right-1 -top-1 h-5 w-5 rounded-full" />
          </span>

          {/* User Avatar and Name Skeleton */}
          <div
            className={cn(
              "relative flex items-center gap-2 cursor-default rounded-xl p-2 border"
            )}
          >
            {/* Skeleton for Avatar */}
            <Skeleton className="h-10 w-10 rounded-full" />
            {/* Skeleton for Online status indicator */}
            <Skeleton className="absolute top-1 h-3 w-3 rounded-full border-2 border-background ltr:left-1 rtl:right-1" />

            {/* Skeleton for User Name and Role/Greeting (hidden on mobile, visible on md+) */}
            <div className="hidden flex-col items-end space-y-1 md:flex">
              <Skeleton className="h-4 w-[100px]" />
              <Skeleton className="h-3 w-[70px]" />
            </div>
            <ChevronDownIcon className="h-5 w-5 text-muted-foreground" />
          </div>
        </div>
      </div>
      {/* Dropdowns are not rendered in the skeleton version */}
    </div>
  );
};

PlatformHeaderSkeleton.displayName = "PlatformHeaderSkeleton";

export default PlatformHeader;
