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
  CheckIcon,
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
  | "exams"
  | null; // Added "exams" for the new dropdown

// Define exam types
type ExamType = "qudurat" | "tahsili" | "step" | "itc" | "cbc" | "petroleum" | "toefl" | "mawhiba";

const examOptions = {
  available: [
    { id: "qudurat" as ExamType, label: "إختبار القدرات", available: true },
    { id: "tahsili" as ExamType, label: "إختبار التحصيلي", available: true },
  ],
  comingSoon: [
    { id: "step" as ExamType, label: "إختبار STEP", available: false },
    { id: "itc" as ExamType, label: "إختبار ITC", available: false },
    { id: "cbc" as ExamType, label: "إختبار CBC", available: false },
    { id: "petroleum" as ExamType, label: "إختبار قبول البترول", available: false },
    { id: "toefl" as ExamType, label: "إختبار TOEFL", available: false },
    { id: "mawhiba" as ExamType, label: "إختبار موهبة", available: false },
  ]
};

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
    
    // State for selected exam
    const [selectedExam, setSelectedExam] = useState<ExamType>("qudurat");

    // Refs for triggers
    const streakTriggerRef = useRef<HTMLSpanElement>(null);
    const pointsTriggerRef = useRef<HTMLSpanElement>(null);
    const giftTriggerRef = useRef<HTMLSpanElement>(null);
    const notificationsTriggerRef = useRef<HTMLSpanElement>(null);
    const userProfileTriggerRef = useRef<HTMLDivElement>(null);
    const examsTriggerRef = useRef<HTMLDivElement>(null);

    // Refs for dropdowns
    const streakDropdownRef = useRef<HTMLDivElement>(null);
    const pointsDropdownRef = useRef<HTMLDivElement>(null);
    const giftDropdownRef = useRef<HTMLDivElement>(null);
    const notificationsDropdownRef = useRef<HTMLDivElement>(null);
    const userProfileDropdownRef = useRef<HTMLDivElement>(null);
    const examsDropdownRef = useRef<HTMLDivElement>(null);

    const handleToggleDropdown = (id: NonNullable<DropdownId>) => {
      setActiveDropdownId((prevId) => (prevId === id ? null : id));
    };

    const closeAllDropdowns = () => {
      setActiveDropdownId(null);
    };

    const handleSelectExam = (examId: ExamType) => {
      setSelectedExam(examId);
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
    useOnClickOutside(
      examsDropdownRef,
      examsTriggerRef,
      closeAllDropdowns,
      activeDropdownId === "exams"
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

    // Get current selected exam label
    const getSelectedExamLabel = () => {
      const allExams = [...examOptions.available, ...examOptions.comingSoon];
      return allExams.find(exam => exam.id === selectedExam)?.label || "إختيار إختبار";
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
      >
        
        <div className="flex flex-col-reverse items-center justify-between gap-6 p-4 lg:h-[70px] lg:flex-row lg:gap-0">
          {/* Search Bar */}
          <div className="flex items-center justify-center gap-3">
            <div className="bg-primary px-3 py-2 text-white text-[14px] rounded-[8px] hover:bg-primary/90 transition-all">
              <Link href="/">العودة إلى الرئيسية</Link>
            </div>
            
            {/* Exam Dropdown */}
            <div className="relative">
              <div
                ref={examsTriggerRef}
                onClick={() => handleToggleDropdown("exams")}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 text-[14px] rounded-[8px] border cursor-pointer transition-all",
                  activeDropdownId === "exams" 
                    ? "bg-muted dark:bg-muted/50 border-primary" 
                    : "hover:bg-muted dark:hover:bg-muted/50"
                )}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === "Enter" && handleToggleDropdown("exams")}
              >
                <span>{getSelectedExamLabel()}</span>
                <ChevronDownIcon className={cn(
                  "h-4 w-4 transition-transform",
                  activeDropdownId === "exams" && "rotate-180"
                )} />
              </div>
              
              {/* Dropdown Menu */}
              {activeDropdownId === "exams" && (
                <div
                  ref={examsDropdownRef}
                  className="absolute top-full mt-2 w-[250px] rounded-lg border bg-background shadow-lg z-50 overflow-hidden"
                >
                  <div className="p-2">
                    {/* Currently Selected */}
                    <div className="text-xs text-muted-foreground px-2 py-1 mb-1">
                      المختار حاليا
                    </div>
                    
                    {/* Available Exams */}
                    {examOptions.available.map((exam) => (
                      <div
                        key={exam.id}
                        onClick={() => handleSelectExam(exam.id)}
                        className={cn(
                          "flex items-center justify-between px-3 py-2 rounded-md cursor-pointer transition-all",
                          selectedExam === exam.id 
                            ? "bg-primary/10 text-primary" 
                            : "hover:bg-muted"
                        )}
                      >
                        <span className="text-sm">{exam.label}</span>
                        {selectedExam === exam.id && (
                          <CheckIcon className="h-4 w-4 text-primary" />
                        )}
                      </div>
                    ))}
                    
                    {/* Divider */}
                    <div className="my-2 border-t border-border" />
                    
                    {/* Coming Soon Section */}
                    <div className="text-xs text-muted-foreground px-2 py-1 mb-1">
                      قريباً
                    </div>
                    
                    {/* Coming Soon Exams */}
                    {examOptions.comingSoon.map((exam) => (
                      <div
                        key={exam.id}
                        className="flex items-center justify-between px-3 py-2 rounded-md opacity-50 cursor-not-allowed"
                      >
                        <span className="text-sm text-muted-foreground">{exam.label}</span>
                        <span className="text-xs bg-muted px-2 py-0.5 rounded-full">
                          قريباً
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

         <div className="flex flex-col-reverse items-center justify-around gap-6 p-0 lg:h-[70px] lg:flex-row lg:gap-0">
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
