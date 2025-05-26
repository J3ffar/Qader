"use client";
import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import {
  Bars3Icon,
  XMarkIcon,
  UserIcon as UserSolidIcon, // For login button
  UserPlusIcon,
  HomeIcon,
  BookOpenIcon,
  PencilIcon,
  UsersIcon,
  QuestionMarkCircleIcon,
  ChatBubbleOvalLeftEllipsisIcon,
  ArrowRightOnRectangleIcon, // For Logout
} from "@heroicons/react/24/solid"; // Assuming you want solid icons for some
import { UserCircleIcon } from "@heroicons/react/24/outline"; // For avatar fallback or generic user icon

import { Button } from "@/components/ui/button"; // Still useful for structure
import { ThemeToggle } from "@/components/ui/theme-toggle";
import LoginModal from "@/components/auth/LoginModal";
import SignupModal from "@/components/auth/SignupModal";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuthStore } from "@/store/auth.store";
import { PATHS } from "@/constants/paths"; // Assuming this is set up
import { toast } from "sonner"; // For logout toast

// Using your original navLinks structure
const navLinks = [
  { name: "الرئيسية", ref: PATHS.HOME || "/", isHidden: false, icon: HomeIcon },
  {
    name: "قصتنا",
    ref: PATHS.ABOUT || "/about",
    isHidden: false,
    icon: BookOpenIcon,
  },
  {
    name: "شركاء النجاح",
    ref: PATHS.PARTNERS || "/partners",
    isHidden: false,
    icon: UsersIcon,
  },
  {
    name: "صفحة المذاكرة",
    ref: PATHS.STUDY_PREVIEW || "/study-preview",
    isHidden: false,
    icon: PencilIcon,
  },
  {
    name: "الأسئلة الشائعة",
    ref: PATHS.FAQ || "/questions",
    isHidden: false, // This controls visibility on desktop as per your original logic
    icon: QuestionMarkCircleIcon,
  },
  {
    name: "تواصل معنا",
    ref: PATHS.CONTACT || "/contact",
    isHidden: false, // This controls visibility on desktop
    icon: ChatBubbleOvalLeftEllipsisIcon,
  },
];

const Navbar = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showSignupModal, setShowSignupModal] = useState(false);
  const [isClient, setIsClient] = useState(false);

  const pathname = usePathname();
  const router = useRouter();
  const { theme } = useTheme(); // ThemeToggle handles setTheme

  const { isAuthenticated, user, logout: storeLogout } = useAuthStore();

  useEffect(() => {
    setIsClient(true);
  }, []);

  const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);
  const closeMobileMenu = useCallback(() => setIsMobileMenuOpen(false), []);

  const openLogin = useCallback(() => {
    setShowLoginModal(true);
    setShowSignupModal(false);
    closeMobileMenu();
  }, [closeMobileMenu]);

  const openSignup = useCallback(() => {
    setShowSignupModal(true);
    setShowLoginModal(false);
    closeMobileMenu();
  }, [closeMobileMenu]);

  const switchToLogin = useCallback(() => {
    setShowSignupModal(false);
    setShowLoginModal(true);
  }, []);

  const switchToSignup = useCallback(() => {
    setShowLoginModal(false);
    setShowSignupModal(true);
  }, []);

  const handleLogout = () => {
    storeLogout();
    toast.success("تم تسجيل الخروج بنجاح.");
    router.push(PATHS.HOME || "/");
    closeMobileMenu();
  };

  const userNavigationAction = () => {
    if (user?.is_super || user?.is_staff) {
      router.push(PATHS.ADMIN_DASHBOARD || "/admin/dashboard");
    } else {
      router.push(PATHS.STUDY_HOME || "/study");
    }
    closeMobileMenu();
  };

  const isDarkTheme = isClient && theme === "dark"; // Ensure client-side check for theme

  const desktopLogoSrc = isDarkTheme
    ? "/images/logodrk.png"
    : "/images/logo.svg";
  const mobileLogoSrc = "/images/logo.png"; // Your specific mobile logo

  // Skeleton/Placeholder for SSR to prevent hydration errors due to theme/auth
  if (!isClient) {
    return (
      <div className="relative z-50">
        <nav className="flex justify-between items-center shadow-lg px-4 sm:px-8 md:px-16 py-4 w-full bg-background max-md:bg-[#074182] md:bg-[#FDFDFD] h-[76px] animate-pulse">
          <div className="hidden max-md:flex w-8 h-8 bg-gray-300 dark:bg-gray-700 rounded"></div>
          <div className="flex-shrink-0 max-md:flex-1 max-md:flex max-md:justify-center max-md:items-center">
            <div className="w-[100px] h-[40px] bg-gray-300 dark:bg-gray-700 rounded"></div>
          </div>
          <ul className="hidden md:flex justify-center items-center gap-3 min-[1120px]:gap-5">
            {[...Array(4)].map((_, i) => (
              <li
                key={i}
                className="w-20 h-5 bg-gray-300 dark:bg-gray-700 rounded"
              ></li>
            ))}
            <div className="w-8 h-8 bg-gray-300 dark:bg-gray-700 rounded-full"></div>
          </ul>
          <div className="hidden md:flex items-center gap-3">
            <div className="w-24 h-10 bg-gray-300 dark:bg-gray-700 rounded-lg"></div>
            <div className="w-32 h-10 bg-gray-300 dark:bg-gray-700 rounded-lg"></div>
          </div>
        </nav>
      </div>
    );
  }

  return (
    <>
      <div className="relative z-50">
        {/* Applying your original nav classes */}
        <nav className="flex justify-between items-center shadow-lg px-4 sm:px-8 md:px-16 py-4 w-full bg-background max-md:bg-[#074182] dark:max-md:bg-[#053061] md:bg-[#FDFDFD] dark:md:bg-[#081028] max-md:flex-row-reverse max-md:gap-6">
          {/* Hamburger Icon */}
          <div className="md:hidden">
            {" "}
            {/* Show only on mobile (max-md implies hidden on md and up) */}
            <button
              onClick={toggleMobileMenu}
              aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
            >
              {isMobileMenuOpen ? (
                <XMarkIcon className="w-8 h-8 text-white md:text-foreground" /> // Adjust color based on background
              ) : (
                <Bars3Icon className="w-8 h-8 text-white md:text-foreground" />
              )}
            </button>
          </div>

          {/* Logo */}
          <div className="flex-shrink-0 max-md:flex-1 max-md:flex max-md:justify-center max-md:items-center">
            <Link href={PATHS.HOME || "/"} onClick={closeMobileMenu}>
              <Image
                alt="Qader Logo"
                src={desktopLogoSrc}
                width={100}
                height={40}
                className="max-md:hidden" // Hidden on mobile
                priority
              />
              <Image
                alt="Qader Logo"
                src={mobileLogoSrc}
                width={100}
                height={40}
                className="md:hidden" // Hidden on desktop
                priority
              />
            </Link>
          </div>

          {/* Desktop Menu */}
          <ul className="hidden md:flex justify-center items-center gap-3 min-[1120px]:gap-5">
            {navLinks.map((item) => (
              <li
                key={item.name}
                className={item.isHidden ? "hidden lg:inline-block" : ""}
              >
                <Link
                  href={item.ref}
                  className={`transition-colors hover:text-[#074182] text-[#074182] dark:text-[#3D93F5] dark:hover:text-[#3D93F5] ${
                    pathname === item.ref
                      ? "font-[600]"
                      : "text-black dark:text-[#FDFDFD]"
                  }`}
                >
                  {item.name}
                </Link>
              </li>
            ))}
          </ul>

          {/* Desktop Auth Area & Theme Toggle */}
          <div className="hidden md:flex items-center gap-3">
            <ThemeToggle />{" "}
            {/* Moved ThemeToggle here to be part of the group */}
            {isAuthenticated && user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    className="relative h-10 w-10 rounded-full p-0"
                  >
                    {" "}
                    {/* Adjusted size slightly */}
                    <Avatar className="h-9 w-9 text-black dark:text-white">
                      <AvatarImage
                        src={user.profile_picture_url || undefined}
                        alt={user.preferred_name || user.full_name || "User"}
                      />
                      <AvatarFallback>
                        {(user.preferred_name || user.full_name || "Q")
                          .substring(0, 1)
                          .toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="start" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">
                        {user.preferred_name || user.full_name}
                      </p>
                      <p className="text-xs leading-none text-muted-foreground">
                        {user.email}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={userNavigationAction}
                    className="cursor-pointer"
                  >
                    {user.is_super || user.is_staff ? (
                      <>
                        <UserCircleIcon className="w-4 h-4 mr-2 rtl:ml-2 rtl:mr-0" />{" "}
                        {/* Example icon */}
                        <span>لوحة التحكم</span>
                      </>
                    ) : (
                      <>
                        <PencilIcon className="w-4 h-4 mr-2 rtl:ml-2 rtl:mr-0" />
                        <span>صفحة المذاكرة</span>
                      </>
                    )}
                  </DropdownMenuItem>
                  {/* Add other items like "Settings" if needed */}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={handleLogout}
                    className="text-red-600 focus:text-red-600 focus:bg-red-500/10 cursor-pointer"
                  >
                    <ArrowRightOnRectangleIcon className="w-4 h-4 mr-2 rtl:ml-2 rtl:mr-0" />
                    <span>تسجيل الخروج</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <>
                <button
                  className="flex gap-2 min-[1120px]:py-3 min-[1120px]:px-4 p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer"
                  onClick={openSignup}
                >
                  <UserPlusIcon className="w-5 h-5 ml-1 rtl:mr-1 rtl:ml-0" />
                  <span className="hidden lg:inline">اشتراك</span>
                </button>
                <button
                  className="hidden lg:flex gap-2 min-[1120px]:py-2.5 min-[1120px]:px-4 p-2 rounded-[8px] bg-transparent border-[1.5px] border-[#074182] text-[#074182] dark:border-[#3D93F5] dark:text-[#3D93F5] font-[600] hover:bg-[#07418211] dark:hover:bg-[#3D93F511] transition-all cursor-pointer"
                  onClick={openLogin}
                >
                  <UserSolidIcon className="w-5 h-5 ml-1 rtl:mr-1 rtl:ml-0" />
                  <span className="lg:inline">تسجيل الدخول</span>
                </button>
              </>
            )}
          </div>
        </nav>

        {/* Mobile Menu - Using your original styling approach */}
        {isMobileMenuOpen && (
          <div className="md:hidden absolute top-full left-0 w-full bg-background dark:bg-[#081028] shadow-md z-40 transition-transform duration-300 ease-in-out">
            <ul className="flex flex-col items-start gap-1 px-5 py-4">
              {navLinks.map((item) => {
                const Icon = item.icon;
                return (
                  <li
                    key={item.name}
                    className="w-full last-of-type:border-b-0 py-3"
                  >
                    <Link
                      href={item.ref}
                      onClick={closeMobileMenu}
                      className={`transition-colors hover:text-[#074182] text-[#074182] dark:text-[#3D93F5] dark:hover:text-[#3D93F5] flex items-center gap-3 w-full ${
                        pathname === item.ref
                          ? "font-[600]"
                          : "text-black dark:text-[#FDFDFD]"
                      }`}
                    >
                      <Icon
                        className={`w-5 h-5 ${
                          pathname === item.ref
                            ? "text-[#074182] dark:text-[#3D93F5]" // Active color
                            : "text-black dark:text-[#FDFDFD]" // Default color
                        }`}
                      />
                      {item.name}
                    </Link>
                  </li>
                );
              })}
            </ul>

            {/* Mobile Auth Buttons / User Info */}
            <div className="flex flex-col items-center gap-4 p-5 border-t border-border">
              {isAuthenticated && user ? (
                <>
                  <div className="flex items-center gap-3 mb-3 w-full justify-center">
                    <Avatar className="h-10 w-10">
                      <AvatarImage
                        src={user.profile_picture_url || undefined}
                        alt={user.preferred_name || user.full_name || "User"}
                      />
                      <AvatarFallback>
                        {(user.preferred_name || user.full_name || "Q")
                          .substring(0, 1)
                          .toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="text-right rtl:text-left">
                      <p className="font-semibold text-sm text-foreground">
                        {user.preferred_name || user.full_name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {user.email}
                      </p>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={userNavigationAction}
                  >
                    {user.is_super || user.is_staff
                      ? "لوحة التحكم"
                      : "صفحة المذاكرة"}
                  </Button>
                  <Button
                    variant="destructive"
                    className="w-full"
                    onClick={handleLogout}
                  >
                    <ArrowRightOnRectangleIcon className="w-5 h-5 ml-2 rtl:mr-2 rtl:ml-0" />
                    تسجيل الخروج
                  </Button>
                </>
              ) : (
                <>
                  <button
                    className="w-full flex justify-center items-center gap-2 py-2.5 px-4 rounded-[8px] bg-transparent border-[1.5px] border-[#074182] text-[#074182] dark:border-[#3D93F5] dark:text-[#3D93F5] font-[600] hover:bg-[#07418211] dark:hover:bg-[#3D93F511] transition-all cursor-pointer"
                    onClick={() => {
                      openLogin();
                    }}
                  >
                    <UserSolidIcon className="w-5 h-5" />
                    <span>تسجيل الدخول</span>
                  </button>
                  <button
                    className="w-full flex justify-center items-center gap-2 py-3 px-4 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer"
                    onClick={() => {
                      openSignup();
                    }}
                  >
                    <UserPlusIcon className="w-5 h-5" />
                    <span>اشتراك</span>
                  </button>
                </>
              )}
              <div className="w-full flex justify-center pt-2">
                <ThemeToggle />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <LoginModal
        show={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onSwitchToSignup={switchToSignup}
      />
      <SignupModal
        show={showSignupModal}
        onClose={() => setShowSignupModal(false)}
        onSwitchToLogin={switchToLogin}
      />
    </>
  );
};

export default Navbar;
