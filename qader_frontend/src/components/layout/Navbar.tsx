"use client";
import React, { useState, useEffect, useCallback, useTransition } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import {
  Bars3Icon,
  XMarkIcon,
  UserIcon as UserSolidIcon,
  UserPlusIcon,
  HomeIcon,
  BookOpenIcon,
  PencilIcon,
  UsersIcon,
  QuestionMarkCircleIcon,
  ChatBubbleOvalLeftEllipsisIcon,
  ArrowRightOnRectangleIcon,
  Cog6ToothIcon,
  LanguageIcon,
} from "@heroicons/react/24/solid";
import { UserCircleIcon } from "@heroicons/react/24/outline";
import { useLocale, useTranslations } from "next-intl";
import NProgress from "nprogress"; // Import NProgress

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import LoginModal from "@/components/auth/LoginModal";
import SignupModal from "@/components/auth/SignupModal";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuthActions, useAuthStore } from "@/store/auth.store";
import { PATHS } from "@/constants/paths";
import { toast } from "sonner";
import { locales as appLocales, Locale } from "@/config/i18n.config"; // Import Locale type
import { CheckIcon } from "lucide-react";
import { join } from "path";

const Navbar = () => {
  const tNav = useTranslations("Nav");
  const tAuth = useTranslations("Auth");
  const tCommon = useTranslations("Common");

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showSignupModal, setShowSignupModal] = useState(false);
  const [isClient, setIsClient] = useState(false);

  const currentLocale = useLocale() as Locale; // Cast to your Locale type
  const router = useRouter();
  const pathname = usePathname(); // This is the path *without* locale prefix
  const [isPending, startTransition] = useTransition();

  const { theme } = useTheme();

  const { isAuthenticated, user } = useAuthStore();
  const { logout: storeLogout } = useAuthActions();

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Effect to handle NProgress state based on isPending from useTransition
  useEffect(() => {
    if (isPending) {
      NProgress.start();
    } else {
      NProgress.done();
    }
    // Cleanup function for NProgress when component unmounts or isPending changes
    return () => {
      NProgress.done();
    };
  }, [isPending]);

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
    toast.success(tAuth("logoutSuccess"));
    router.push(PATHS.HOME);
    closeMobileMenu();
  };

  const userNavigationAction = () => {
    if (user?.is_super || user?.is_staff) router.push(PATHS.ADMIN_DASHBOARD);
    else router.push(PATHS.STUDY.HOME);
    closeMobileMenu();
  };

  const navLinks = [
    // ... (your navLinks definition remains the same)
    {
      nameKey: "home" as const,
      ref: PATHS.HOME,
      isHidden: false,
      icon: HomeIcon,
    },
    {
      nameKey: "about" as const,
      ref: PATHS.ABOUT,
      isHidden: false,
      icon: BookOpenIcon,
    },
    {
      nameKey: "partners" as const,
      ref: PATHS.PARTNERS,
      isHidden: false,
      icon: UsersIcon,
    },
    {
      nameKey: "studyPreview" as const,
      ref: PATHS.STUDY_PREVIEW,
      isHidden: false,
      icon: PencilIcon,
    },
    {
      nameKey: "faq" as const,
      ref: PATHS.FAQ,
      isHidden: false,
      icon: QuestionMarkCircleIcon,
    },
    {
      nameKey: "contact" as const,
      ref: PATHS.CONTACT,
      isHidden: false,
      icon: ChatBubbleOvalLeftEllipsisIcon,
    },
  ];

  const isDarkTheme = isClient && theme === "dark";
  const desktopLogoSrc = isDarkTheme
    ? "/images/logodrk.png"
    : "/images/logo.svg";
  const mobileLogoSrc = "/images/logo.png"; // Assuming this is a universal mobile logo

  const handleLocaleChange = (newLocale: string) => {
    let newPathname = "";

    if (pathname.startsWith("/en")) newPathname = pathname.slice(3);
    else if (pathname.startsWith("/ar")) newPathname = pathname.slice(3);
    else newPathname = pathname;
    startTransition(() => {
      router.replace(join(newLocale, newPathname));
      // router.refresh(); // Optional: if you need to re-fetch server components on the same page
    });
    // NProgress is handled by the useEffect watching `isPending`
    closeMobileMenu();
  };

  const LanguageSwitcher = ({
    inMobileMenu = false,
  }: {
    inMobileMenu?: boolean;
  }) => (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="default" // Changed to ghost for better visual consistency with ThemeToggle
          size={inMobileMenu ? "default" : "icon"}
          className={
            inMobileMenu
              ? "w-full justify-start gap-2 text-foreground"
              : "text-foreground"
          }
          aria-label={tCommon("language")}
        >
          <LanguageIcon className="h-5 w-5 text-white" />
          {inMobileMenu && <span>{tCommon("language")}</span>}
          <span className="sr-only">{tCommon("language")}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>{tCommon("selectLanguage")}</DropdownMenuLabel>{" "}
        {/* More specific label */}
        <DropdownMenuSeparator />
        <DropdownMenuRadioGroup
          value={currentLocale}
          onValueChange={(newLocale) => {
            if (newLocale !== currentLocale) {
              handleLocaleChange(newLocale);
            }
          }}
        >
          {appLocales.map((locale) => (
            <DropdownMenuRadioItem
              key={locale}
              value={locale}
              disabled={isPending}
              className="cursor-pointer"
            >
              {locale === "ar"
                ? tCommon("arabic")
                : locale === "en"
                ? tCommon("english")
                : locale.toUpperCase()}
              {/* Shadcn's DropdownMenuRadioItem should handle the checkmark internally based on value match */}
              {/* If not, your explicit CheckIcon logic is fine: */}
              {currentLocale === locale && !isPending && (
                <CheckIcon className="ms-auto h-4 w-4 rtl:me-auto rtl:ms-0" />
              )}
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );

  if (!isClient) {
    // ... (Skeleton remains the same)
    return (
      <div className="relative z-50">
        <nav className="flex h-[76px] w-full animate-pulse items-center justify-between bg-background px-4 py-4 shadow-lg max-md:bg-[#074182] sm:px-8 md:bg-[#FDFDFD] md:px-16">
          <div className="hidden h-8 w-8 rounded bg-gray-300 dark:bg-gray-700 max-md:flex"></div>
          <div className="flex-shrink-0 justify-start max-md:flex max-md:items-center max-md:justify-center">
            <div className="h-[40px] w-[100px] rounded bg-gray-300 dark:bg-gray-700"></div>
          </div>
          <ul className="hidden items-center justify-center gap-3 md:flex min-[1120px]:gap-5">
            {[...Array(4)].map((_, i) => (
              <li
                key={i}
                className="h-5 w-20 rounded bg-gray-300 dark:bg-gray-700"
              ></li>
            ))}
            <div className="h-8 w-8 rounded-full bg-gray-300 dark:bg-gray-700"></div>{" "}
            {/* Language Switcher Skeleton */}
            <div className="h-8 w-8 rounded-full bg-gray-300 dark:bg-gray-700"></div>{" "}
            {/* Theme Toggle Skeleton */}
          </ul>
          <div className="hidden items-center gap-3 md:flex">
            <div className="h-10 w-24 rounded-lg bg-gray-300 dark:bg-gray-700"></div>
            <div className="h-10 w-32 rounded-lg bg-gray-300 dark:bg-gray-700"></div>
          </div>
        </nav>
      </div>
    );
  }

  return (
    <>
      <div className="relative z-50">
        <nav className="flex w-full items-center justify-between bg-background px-4 py-4 shadow-lg max-md:flex-row-reverse max-md:gap-6 max-md:bg-[#074182] dark:max-md:bg-[#053061] sm:px-8 md:bg-[#FDFDFD] md:px-16 dark:md:bg-[#081028]">
          {/* ... (Mobile menu button and Logo remain the same) ... */}
          <div className="md:hidden">
            <button
              onClick={toggleMobileMenu}
              aria-label={
                isMobileMenuOpen ? tNav("closeMenu") : tNav("openMenu")
              }
            >
              {isMobileMenuOpen ? (
                <XMarkIcon className="h-8 w-8 text-white md:text-foreground" />
              ) : (
                <Bars3Icon className="h-8 w-8 text-white md:text-foreground" />
              )}
            </button>
          </div>

          <div className="flex-shrink-0 justify-start max-md:flex max-md:items-center max-md:justify-center">
            <Link href={PATHS.HOME} onClick={closeMobileMenu}>
              <Image
                alt={tNav("qaderLogoAlt")}
                src={desktopLogoSrc}
                width={100}
                height={40}
                className="max-md:hidden"
                priority
              />
              <Image
                alt={tNav("qaderLogoAlt")}
                src={mobileLogoSrc}
                width={100}
                height={40}
                className="md:hidden"
                priority
              />
            </Link>
          </div>

          <ul className="hidden items-center justify-center gap-3 md:flex min-[1120px]:gap-5">
            {navLinks.map((item) => (
              <li
                key={item.nameKey}
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
                  {tNav(item.nameKey)}
                </Link>
              </li>
            ))}
          </ul>

          <div className="hidden items-center gap-2 md:flex">
            {" "}
            {/* Reduced gap slightly */}
            <ThemeToggle />
            <LanguageSwitcher /> {/* Ensure this is rendered */}
            {isAuthenticated && user ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="relative h-10 w-10 rounded-full p-0"
                  >
                    <Avatar className="h-9 w-9 text-black dark:text-white">
                      <AvatarImage
                        src={user.profile_picture_url || undefined}
                        alt={tNav("userAvatarAlt")}
                      />
                      <AvatarFallback>
                        {(user.preferred_name || user.full_name || "Q")
                          .substring(0, 1)
                          .toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  className="w-56"
                  align={currentLocale === "ar" ? "start" : "end"}
                  forceMount
                >
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
                        <UserCircleIcon className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                        <span>{tNav("dashboard")}</span>
                      </>
                    ) : (
                      <>
                        <PencilIcon className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                        <span>{tNav("studyPreview")}</span>
                      </>
                    )}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => {
                      router.push(PATHS.SETTINGS.HOME);
                      closeMobileMenu();
                    }}
                    className="cursor-pointer"
                  >
                    <Cog6ToothIcon className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />{" "}
                    <span>{tNav("settings")}</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={handleLogout}
                    className="cursor-pointer text-red-600 focus:bg-red-500/10 focus:text-red-600"
                  >
                    <ArrowRightOnRectangleIcon className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />
                    <span>{tAuth("logout")}</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <>
                <button
                  className="flex cursor-pointer gap-2 rounded-[8px] bg-[#074182] p-2 font-[600] text-[#FDFDFD] transition-all hover:bg-[#074182DF] dark:bg-[#074182] dark:hover:bg-[#074182DF] min-[1120px]:px-4 min-[1120px]:py-3"
                  onClick={openSignup}
                  aria-label={tAuth("signup")}
                >
                  <UserPlusIcon className="ms-1 h-5 w-5 rtl:me-1 rtl:ms-0" />
                  <span className="hidden lg:inline">{tAuth("signup")}</span>
                </button>
                <button
                  className="hidden cursor-pointer gap-2 rounded-[8px] border-[1.5px] border-[#074182] bg-transparent p-2 font-[600] text-[#074182] transition-all hover:bg-[#07418211] dark:border-[#3D93F5] dark:text-[#3D93F5] dark:hover:bg-[#3D93F511] lg:flex min-[1120px]:px-4 min-[1120px]:py-2.5"
                  onClick={openLogin}
                  aria-label={tAuth("login")}
                >
                  <UserSolidIcon className="ms-1 h-5 w-5 rtl:me-1 rtl:ms-0" />
                  <span className="lg:inline">{tAuth("login")}</span>
                </button>
              </>
            )}
          </div>
        </nav>

        {isMobileMenuOpen && (
          <div className="absolute left-0 top-full z-40 w-full bg-background shadow-md transition-transform duration-300 ease-in-out dark:bg-[#081028] md:hidden">
            {/* ... (Mobile nav links remain the same) ... */}
            <ul className="flex flex-col items-start gap-1 px-5 py-4">
              {navLinks.map((item) => {
                const Icon = item.icon;
                return (
                  <li
                    key={item.nameKey}
                    className="w-full py-3 last-of-type:border-b-0"
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
                            ? "text-[#074182] dark:text-[#3D93F5]"
                            : "text-black dark:text-[#FDFDFD]"
                        }`}
                      />
                      {tNav(item.nameKey)}
                    </Link>
                  </li>
                );
              })}
            </ul>

            <div className="flex flex-col items-center gap-4 border-t border-border p-5">
              {/* ... (Mobile auth buttons / User info remain the same) ... */}
              {isAuthenticated && user ? (
                <>
                  <div className="mb-3 flex w-full items-center justify-center gap-3">
                    <Avatar className="h-10 w-10">
                      <AvatarImage
                        src={user.profile_picture_url || undefined}
                        alt={tNav("userAvatarAlt")}
                      />
                      <AvatarFallback>
                        {(user.preferred_name || user.full_name || "Q")
                          .substring(0, 1)
                          .toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div className="text-start rtl:text-end">
                      {" "}
                      {/* Ensure text alignment respects LTR/RTL */}
                      <p className="text-sm font-semibold text-foreground">
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
                      ? tNav("dashboard")
                      : tNav("studyPreview")}
                  </Button>
                  {/* Add Settings Link to Mobile Menu */}
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      router.push(PATHS.SETTINGS.HOME);
                      closeMobileMenu();
                    }}
                  >
                    <Cog6ToothIcon className="me-2 h-4 w-4 rtl:me-0 rtl:ms-2" />{" "}
                    {tNav("settings")}
                  </Button>
                  <Button
                    variant="destructive"
                    className="w-full"
                    onClick={handleLogout}
                  >
                    <ArrowRightOnRectangleIcon className="ms-2 h-5 w-5 rtl:me-2 rtl:ms-0" />
                    {tAuth("logout")}
                  </Button>
                </>
              ) : (
                <>
                  <button
                    className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-[8px] border-[1.5px] border-[#074182] bg-transparent px-4 py-2.5 font-[600] text-[#074182] transition-all hover:bg-[#07418211] dark:border-[#3D93F5] dark:text-[#3D93F5] dark:hover:bg-[#3D93F511]"
                    onClick={openLogin}
                    aria-label={tAuth("login")}
                  >
                    {" "}
                    <UserSolidIcon className="h-5 w-5" />{" "}
                    <span>{tAuth("login")}</span>
                  </button>
                  <button
                    className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-[8px] bg-[#074182] px-4 py-3 font-[600] text-[#FDFDFD] transition-all hover:bg-[#074182DF] dark:bg-[#074182] dark:hover:bg-[#074182DF]"
                    onClick={openSignup}
                    aria-label={tAuth("signup")}
                  >
                    {" "}
                    <UserPlusIcon className="h-5 w-5" />{" "}
                    <span>{tAuth("signup")}</span>
                  </button>
                </>
              )}
              {/* Language Switcher and Theme Toggle in Mobile Menu */}
              <div className="mt-4 w-full space-y-3 border-t border-border pt-4">
                <LanguageSwitcher inMobileMenu={true} />
                <div className="flex w-full justify-start">
                  {" "}
                  {/* Align theme toggle like language switcher */}
                  <ThemeToggle />{" "}
                  {/* Assuming ThemeToggle also has a "full width" or similar mode if needed, or style appropriately */}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

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
