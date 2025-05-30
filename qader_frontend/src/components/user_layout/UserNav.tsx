"use client";

import { useState, useRef } from "react";
import Image from "next/image";
import { useTranslations } from "next-intl";
import {
  MagnifyingGlassIcon,
  StarIcon,
  GiftIcon,
  BellIcon,
  ChevronDownIcon,
} from "@heroicons/react/24/outline";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthCore } from "@/store/auth.store";
import { cn } from "@/lib/utils";
import { useOnClickOutside } from "@/hooks/useOnClickOutside"; // Import the custom hook

import Shapcontain from "@/components/sections/contains-of-user-nav/ShapContain";
import StarContain from "@/components/sections/contains-of-user-nav/StarContain";
import GiftContain from "@/components/sections/contains-of-user-nav/GiftContain";
import BellShap from "@/components/sections/contains-of-user-nav/BellContain";
import UserContain from "@/components/sections/contains-of-user-nav/UserContain";

interface UserNavbarProps {
  isOpen: boolean; // Sidebar state
}

type DropdownId = "star" | "gems" | "gift" | "bell" | "userProfile" | null;

const UserNavbar = ({ isOpen }: UserNavbarProps) => {
  const tNav = useTranslations("Nav.UserNav");
  const { user, isAuthenticated } = useAuthCore();

  const [activeDropdownId, setActiveDropdownId] = useState<DropdownId>(null);
  // For GiftContain's internal state
  const [giftActiveSection, setGiftActiveSection] = useState<
    "invite" | "store"
  >("invite");

  // Refs for triggers
  const starTriggerRef = useRef<HTMLSpanElement>(null);
  const gemsTriggerRef = useRef<HTMLSpanElement>(null);
  const giftTriggerRef = useRef<HTMLSpanElement>(null);
  const bellTriggerRef = useRef<HTMLSpanElement>(null);
  const userProfileTriggerRef = useRef<HTMLDivElement>(null);

  // Refs for dropdowns
  const starDropdownRef = useRef<HTMLDivElement>(null);
  const gemsDropdownRef = useRef<HTMLDivElement>(null);
  const giftDropdownRef = useRef<HTMLDivElement>(null);
  const bellDropdownRef = useRef<HTMLDivElement>(null);
  const userProfileDropdownRef = useRef<HTMLDivElement>(null);

  const handleToggleDropdown = (id: NonNullable<DropdownId>) => {
    setActiveDropdownId((prevId) => (prevId === id ? null : id));
  };

  const closeAllDropdowns = () => {
    setActiveDropdownId(null);
  };

  // Apply click outside hook for each dropdown
  useOnClickOutside(
    starDropdownRef,
    starTriggerRef,
    closeAllDropdowns,
    activeDropdownId === "star"
  );
  useOnClickOutside(
    gemsDropdownRef,
    gemsTriggerRef,
    closeAllDropdowns,
    activeDropdownId === "gems"
  );
  useOnClickOutside(
    giftDropdownRef,
    giftTriggerRef,
    closeAllDropdowns,
    activeDropdownId === "gift"
  );
  useOnClickOutside(
    bellDropdownRef,
    bellTriggerRef,
    closeAllDropdowns,
    activeDropdownId === "bell"
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
        {/* Search Bar */}
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
            ref={starTriggerRef}
            className={cn(
              "flex items-center gap-1 cursor-pointer rounded-xl p-2 border",
              activeDropdownId === "star"
                ? "bg-muted dark:bg-muted/50"
                : "hover:bg-muted dark:hover:bg-muted/50"
            )}
            onClick={() => handleToggleDropdown("star")}
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
            ref={gemsTriggerRef}
            className={cn(
              "flex items-center gap-1 cursor-pointer rounded-xl p-2 border",
              activeDropdownId === "gems"
                ? "bg-muted dark:bg-muted/50"
                : "hover:bg-muted dark:hover:bg-muted/50"
            )}
            onClick={() => handleToggleDropdown("gems")}
          >
            <Image
              src="/images/hexagon.png"
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
            ref={giftTriggerRef}
            className={cn(
              "relative cursor-pointer rounded-xl p-2 border",
              activeDropdownId === "gift"
                ? "bg-muted dark:bg-muted/50"
                : "hover:bg-muted dark:hover:bg-muted/50"
            )}
            onClick={() => handleToggleDropdown("gift")}
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
            ref={bellTriggerRef}
            className={cn(
              "relative cursor-pointer rounded-xl p-2 rtl:mr-4 ltr:ml-4 border",
              activeDropdownId === "bell"
                ? "bg-muted dark:bg-muted/50"
                : "hover:bg-muted dark:hover:bg-muted/50"
            )}
            onClick={() => handleToggleDropdown("bell")}
          >
            <BellIcon className="h-6 w-6" />
            {isAuthenticated && user && user.unread_notifications_count > 0 && (
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
              <div className="h-10 w-10 rounded-full bg-muted" />
            )}
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

      {/* Conditionally render dropdowns and pass refs */}
      {/* It's important that the child components accept a ref and forward it to their root element */}
      <div ref={starDropdownRef}>
        <StarContain showStarContainer={activeDropdownId === "star"} />
      </div>
      <div ref={gemsDropdownRef}>
        <Shapcontain showShapContain={activeDropdownId === "gems"} />
      </div>
      <div ref={giftDropdownRef}>
        <GiftContain
          isVisible={activeDropdownId === "gift"}
          activeSection={giftActiveSection}
          setActiveSection={setGiftActiveSection}
        />
      </div>
      <div ref={bellDropdownRef}>
        <BellShap showBellDropdown={activeDropdownId === "bell"} />
      </div>
      <div ref={userProfileDropdownRef}>
        <UserContain showUserContain={activeDropdownId === "userProfile"} />
      </div>
    </div>
  );
};

export default UserNavbar;
