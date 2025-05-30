"use client";

import { useState } from "react";
import Image from "next/image";
import { useTranslations } from "next-intl";
import {
  MagnifyingGlassIcon,
  StarIcon,
  GiftIcon,
  BellIcon,
  ChevronDownIcon,
} from "@heroicons/react/24/outline";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"; // Shadcn Avatar
import { Skeleton } from "@/components/ui/skeleton"; // Shadcn Skeleton
import { useAuthCore } from "@/store/auth.store"; // Auth store hook

import Shapcontain from "@/components/sections/contains-of-user-nav/ShapContain";
import StarContain from "@/components/sections/contains-of-user-nav/StarContain";
import GiftContain from "@/components/sections/contains-of-user-nav/GiftContain";
import BellShap from "@/components/sections/contains-of-user-nav/BellContain";
import UserContain from "@/components/sections/contains-of-user-nav/UserContain";
import { cn } from "@/lib/utils"; // For conditional classes

interface UserNavbarProps {
  isOpen: boolean; // Sidebar state
}

const UserNavbar = ({ isOpen }: UserNavbarProps) => {
  const tNav = useTranslations("Nav.UserNav"); // For "Good morning" etc.
  const { user, isAuthenticated } = useAuthCore();

  const [showStarContainer, setShowStarContainer] = useState(false);
  const [showShapContain, setShowShapContain] = useState(false);
  const [activeSection, setActiveSection] = useState<"invite" | "store">(
    "invite"
  );
  const [isVisible, setIsVisible] = useState(false); // For GiftContain
  const [showBellDropdown, setShowBellDropdown] = useState(false);
  const [showUserContain, setShowUserContain] = useState(false);

  const toggleStarContainer = () => setShowStarContainer((prev) => !prev);
  const toggleShapContain = () => setShowShapContain((prev) => !prev);
  const toggleVisibility = () => setIsVisible((prev) => !prev);
  const toggleBellDropdown = () => setShowBellDropdown((prev) => !prev);
  const toggleUserContain = () => setShowUserContain((prev) => !prev);

  const getInitials = (name: string | undefined | null): string => {
    if (!name) return "Q"; // Qader initials
    return name
      .split(" ")
      .map((n) => n[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  };

  // Style for the main navbar div based on sidebar state
  // Note: The original fixed values for `right` seemed unusual.
  // A common pattern would be setting `left` based on sidebar width.
  // I'll keep the original logic for now as requested, but this might need review.
  const navbarStyle = {
    right: isOpen ? "110px" : "50px", // This assumes specific sidebar behavior
    left: "0px", // This makes it overlay the sidebar partially
    // A more typical approach if sidebar is fixed width:
    // left: isOpen ? "220px" : "100px",
    // right: "0px",
  };

  return (
    <div
      className="top-0 z-40 flex h-auto flex-col border-b-[0.5px] border-border bg-background pl-5 pr-5 shadow-sm transition-all duration-300 dark:border-gray-700 max-md:py-3"
      style={navbarStyle}
    >
      {/* Input + Search Button */}
      <div className="flex flex-col-reverse items-center justify-between gap-6 p-4 lg:h-[70px] lg:flex-row lg:gap-0">
        {/* Search Bar - Assuming this is fine as is */}
        <div className="flex w-full flex-1 items-center justify-center lg:w-auto">
          <div className="flex w-full max-w-md items-center overflow-hidden rounded-lg border bg-card dark:bg-transparent">
            <MagnifyingGlassIcon className="mr-2 h-5 w-5 text-muted-foreground" />
            <input
              type="text"
              placeholder={tNav("searchPlaceholder")}
              className="flex-1 bg-transparent p-2 text-right placeholder:text-muted-foreground focus:outline-none"
            />
          </div>
          <button className="ml-2 mr-2 rounded-lg bg-primary p-2 text-primary-foreground transition hover:bg-primary/90">
            <MagnifyingGlassIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Icons: Points, Streak, Gift */}
        <div className="flex items-center gap-4">
          {/* Streak (Stars) */}
          <span
            className={cn(
              "flex items-center gap-1 cursor-pointer rounded-xl p-2 border",
              showStarContainer
                ? "bg-muted dark:bg-muted/50"
                : "hover:bg-muted dark:hover:bg-muted/50"
            )}
            onClick={toggleStarContainer}
          >
            <StarIcon className="h-6 w-6 text-yellow-500" />
            {isAuthenticated && !user ? (
              <Skeleton className="h-4 w-6" />
            ) : (
              user?.current_streak_days ?? 0
            )}
          </span>

          {/* Points (Hexagon/Gems) */}
          <span
            className={cn(
              "flex items-center gap-1 cursor-pointer rounded-xl p-2 border",
              showShapContain
                ? "bg-muted dark:bg-muted/50"
                : "hover:bg-muted dark:hover:bg-muted/50"
            )}
            onClick={toggleShapContain}
          >
            <Image
              src="/images/hexagon.png" // Ensure this image is present
              width={25}
              height={25}
              alt="gems"
            />
            {isAuthenticated && !user ? (
              <Skeleton className="h-4 w-8" />
            ) : (
              user?.points ?? 0
            )}
          </span>

          {/* Gift */}
          <span
            className={cn(
              "relative cursor-pointer rounded-xl p-2 border",
              isVisible
                ? "bg-muted dark:bg-muted/50"
                : "hover:bg-muted dark:hover:bg-muted/50"
            )}
            onClick={toggleVisibility}
          >
            <GiftIcon className="h-6 w-6 text-pink-500" />
            {/* Assuming gift notification logic is separate */}
            <span className="absolute right-1 top-1 h-3 w-3 rounded-full border-2 border-background bg-red-500"></span>
          </span>
        </div>

        {/* Notifications and User Profile */}
        <div className="flex items-center gap-4">
          {/* Bell Icon */}
          <span
            className={cn(
              "relative cursor-pointer rounded-xl p-2 rtl:mr-4 ltr:ml-4 border",
              showBellDropdown
                ? "bg-muted dark:bg-muted/50"
                : "hover:bg-muted dark:hover:bg-muted/50"
            )}
            onClick={toggleBellDropdown}
          >
            <BellIcon className="h-6 w-6" />
            {isAuthenticated && user && user.unread_notifications_count > 0 && (
              <span className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs text-white">
                {user.unread_notifications_count > 9
                  ? "9+"
                  : user.unread_notifications_count}
              </span>
            )}
            {isAuthenticated &&
              !user && ( // Skeleton for notification count badge
                <Skeleton className="absolute -right-1 -top-1 h-5 w-5 rounded-full" />
              )}
          </span>

          {/* User Avatar and Name */}
          <div
            onClick={toggleUserContain}
            className={cn(
              "relative flex items-center gap-2 cursor-pointer rounded-xl p-2 border",
              showUserContain
                ? "bg-muted dark:bg-muted/50"
                : "hover:bg-muted dark:hover:bg-muted/50"
            )}
          >
            {isAuthenticated && !user ? (
              <Skeleton className="h-10 w-10 rounded-full" />
            ) : user ? (
              <Avatar className="h-10 w-10">
                <AvatarImage
                  src={user.profile_picture_url || undefined}
                  alt={user.full_name || user.username || "User"}
                />
                <AvatarFallback>
                  {getInitials(user.full_name || user.username)}
                </AvatarFallback>
              </Avatar>
            ) : (
              // Placeholder for non-authenticated or if user somehow is null despite isAuthenticated (should not happen)
              <div className="h-10 w-10 rounded-full bg-muted" />
            )}
            {/* Online status indicator - assuming logic is external or fixed for now */}
            {isAuthenticated && user && (
              <span className="absolute top-1 h-3 w-3 rounded-full border-2 border-background bg-green-500 ltr:left-1 rtl:right-1"></span>
            )}

            {isAuthenticated && !user ? (
              <div className="hidden flex-col items-end space-y-1 md:flex">
                <Skeleton className="h-4 w-[100px]" />
                <Skeleton className="h-3 w-[70px]" />
              </div>
            ) : user ? (
              <div className="hidden flex-col items-end max-md:hidden md:flex">
                <p className="text-sm font-medium">
                  {user.preferred_name || user.full_name || user.username}
                </p>
                <p className="text-xs text-muted-foreground">
                  {tNav("greeting")}
                </p>
              </div>
            ) : null}
            <ChevronDownIcon className="h-5 w-5 text-muted-foreground" />
          </div>
        </div>
      </div>

      {/* Other Containers (Popovers/Dropdowns) */}
      <Shapcontain showShapContain={showShapContain} />
      <GiftContain
        isVisible={isVisible}
        activeSection={activeSection}
        setActiveSection={setActiveSection}
      />
      <StarContain showStarContainer={showStarContainer} />
      <BellShap showBellDropdown={showBellDropdown} />
      <UserContain showUserContain={showUserContain} />
    </div>
  );
};

export default UserNavbar;
