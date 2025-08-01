"use client";

import { useState, useEffect, useMemo } from "react";
import { usePathname } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
// Using Lucide icons for toggle to match preferred stack
import {
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelRightClose,
} from "lucide-react";

import { cn } from "@/lib/utils";
// Updated import path and name
import {
  PLATFORM_SIDEBAR_SECTIONS,
  PLATFORM_SIDEBAR_HOME_ITEM, // Optional home item
  PlatformSidebarNavItem,
} from "@/config/platform-navigation";
import { PATHS } from "@/constants/paths"; // Adjust path
import { Skeleton } from "@/components/ui/skeleton";

interface PlatformSidebarProps {
  isOpen: boolean;
  setIsOpen: (value: boolean) => void;
}

const PlatformSidebar = ({ isOpen, setIsOpen }: PlatformSidebarProps) => {
  const t = useTranslations(); // Root translation for general keys
  const tSidebar = useTranslations("Nav"); // Specific namespace for sidebar keys
  const pathname = usePathname();
  const locale = useLocale();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
    // Optional: Persist sidebar state to localStorage
    // const storedState = localStorage.getItem('sidebarOpen');
    // if (storedState) {
    //   setIsOpen(JSON.parse(storedState));
    // }
  }, []);

  // useEffect(() => {
  //   if (isClient) {
  //     localStorage.setItem('sidebarOpen', JSON.stringify(isOpen));
  //   }
  // }, [isOpen, isClient]);

  // Memoize sections to prevent re-computation if not needed
  const sidebarSections = useMemo(() => PLATFORM_SIDEBAR_SECTIONS, []);
  const homeItem = useMemo(() => PLATFORM_SIDEBAR_HOME_ITEM, []);

  if (!isClient) {
    // Optional: Render a Skeleton sidebar or null
    return (
      <aside
        className={cn(
          "relative z-30 flex min-h-screen flex-col bg-primary text-primary-foreground transition-all duration-300 ease-in-out dark:bg-primary-dark",
          "w-[100px] md:w-[220px]" // Default to wider on md+, or use isOpen for dynamic
        )}
      >
        <div className="flex flex-col items-center py-6">
          <Skeleton className="mb-2 h-[70px] w-[70px] rounded-md md:h-[120px] md:w-[120px]" />
        </div>
        <nav className="flex-1 space-y-3 px-2 py-4">
          {[...Array(3)].map((_, sectionIndex) => (
            <div key={sectionIndex}>
              <Skeleton className="mb-4 hidden h-6 w-3/4 px-4 md:block" />
              {[...Array(3)].map((_, itemIndex) => (
                <div
                  key={itemIndex}
                  className="flex items-center justify-center gap-x-3 px-4 py-3 md:justify-start"
                >
                  <Skeleton className="h-6 w-6 rounded" />
                  <Skeleton className="hidden h-5 w-24 md:block" />
                </div>
              ))}
            </div>
          ))}
        </nav>
      </aside>
    );
  }

  const ToggleIconComponent = isOpen
    ? locale === "ar"
      ? PanelRightClose
      : PanelLeftClose // More descriptive icons
    : locale === "ar"
    ? PanelLeftClose
    : PanelRightClose;

  const renderMenuItem = (item: PlatformSidebarNavItem, isTopLevel = false) => {
    // Normalize href to ensure consistent matching (e.g. remove trailing slash if one has it and other doesn't)
    const normalizedPathname =
      pathname.endsWith("/") && pathname.length > 1
        ? pathname.slice(0, -1)
        : pathname;
    const normalizedItemHref =
      item.href.endsWith("/") && item.href.length > 1
        ? item.href.slice(0, -1)
        : item.href;

    const isActive = item.exactMatch
      ? normalizedPathname === normalizedItemHref
      : normalizedPathname.startsWith(normalizedItemHref);

    const IconComponent = item.icon;

    return (
      <Link
        key={item.labelKey}
        href={item.disabled || item.comingSoon ? "#" : item.href}
        aria-current={isActive ? "page" : undefined}
        onClick={(e) =>
          (item.disabled || item.comingSoon) && e.preventDefault()
        }
        tabIndex={item.disabled || item.comingSoon ? -1 : 0}
        className={cn(
          "block rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
          item.disabled || item.comingSoon ? "cursor-not-allowed" : ""
        )}
      >
        {/* FIX: Changed motion.a to motion.div. The parent <Link> now renders the <a> tag. */}
        <motion.div
          className={cn(
            "flex items-center rounded-md px-3 py-2.5 text-sm transition-colors duration-150",
            isOpen ? "justify-start gap-x-3" : "justify-center",
            item.disabled || item.comingSoon
              ? "cursor-not-allowed text-muted-foreground/70 hover:bg-transparent"
              : isActive
              ? "bg-primary-foreground/20 border-r-4 text-primary-foreground hover:bg-primary-foreground/25 dark:bg-primary-dark-foreground/20 dark:text-primary-dark-foreground dark:hover:bg-primary-dark-foreground/25"
              : "text-primary-foreground/80 hover:bg-primary-foreground/10 hover:text-primary-foreground dark:text-primary-dark-foreground/80 dark:hover:bg-primary-dark-foreground/10 dark:hover:text-primary-dark-foreground",
            isTopLevel && !isOpen && "py-3"
          )}
          whileHover={
            !item.disabled && !item.comingSoon && !isActive
              ? { scale: 1.03 }
              : {}
          }
          animate={isActive ? { scale: 1.0 } : {}}
          transition={{ duration: 0.15 }}
        >
          <IconComponent
            className={cn("h-5 w-5 flex-shrink-0", isOpen ? "me-0" : "mx-auto")}
          />
          <AnimatePresence>
            {isOpen && (
              <motion.span
                initial={{
                  opacity: 0,
                  width: 0,
                  x: locale === "ar" ? 10 : -10,
                }}
                animate={{ opacity: 1, width: "auto", x: 0 }}
                exit={{ opacity: 0, width: 0, x: locale === "ar" ? 10 : -10 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
                className={cn(
                  "overflow-hidden whitespace-nowrap",
                  isActive ? "font-semibold" : "font-medium"
                )}
              >
                {tSidebar(item.labelKey as any)}
                {item.comingSoon && (
                  <span className="text-xs opacity-90 ltr:ml-2 rtl:mr-2">
                    ({tSidebar("PlatformSidebar.items.comingSoonSuffix" as any)}
                    )
                  </span>
                )}
              </motion.span>
            )}
          </AnimatePresence>
        </motion.div>
      </Link>
    );
  };

  return (
    // Use theme variables for colors if you have them defined in globals.css or tailwind.config
    <aside
      className={cn(
        "sticky top-0 bg-primary dark:bg-[#081029] border-l z-50 flex h-screen flex-col text-primary-foreground shadow-lg transition-all duration-300 ease-in-out",
        isOpen ? "w-60" : "w-[72px]" // Slightly wider when open for text, narrower when closed for icons
      )}
      aria-label={tSidebar("PlatformSidebar.sidebarNavigationLabel" as any)} // More generic label
    >
      {/* Toggle Button - Consider making it part of the header or a separate component */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "absolute top-13 z-50 flex h-9 w-9 items-center justify-center rounded-full border border-border bg-background text-foreground shadow-md transition-all duration-200 hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          isOpen
            ? locale === "ar"
              ? "-left-4"
              : "-right-4" // Inside sidebar when open
            : locale === "ar"
            ? "-left-4"
            : "-right-4" // Protruding when closed
          // Vertical centering for the button
        )}
        aria-label={tSidebar(
          isOpen
            ? "PlatformSidebar.toggleClose"
            : ("PlatformSidebar.toggleOpen" as any)
        )}
        aria-expanded={isOpen}
      >
        <ToggleIconComponent className="h-5 w-5 cursor-pointer" />
      </button>

      {/* Logo Section */}
      <div
        className={cn(
          "flex items-center justify-center border-b border-primary-foreground/10 dark:border-primary-dark-foreground/10 ",
          isOpen ? "px-6" : "px-3",
          "h-[var(--header-height,100px)]" // Match header height
        )}
      >
        <Link
          href={`/${locale}${PATHS.STUDY.HOME}`}
          className="block rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          aria-label={tSidebar("PlatformSidebar.logoAlt" as any)}
        >
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={isOpen ? "logo-large" : "logo-small"}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.2 }}
              className="flex items-center justify-center"
            >
              {isOpen ? (
                <Image
                  src="/images/logo/logo-full-light.png" // Example: different logo for light/dark if needed
                  width={130}
                  height={70} // Adjust to your logo's aspect ratio
                  alt={tSidebar("PlatformSidebar.logoAlt" as any)}
                  priority
                  className="dark:hidden"
                />
              ) : (
                <Image
                  src="/images/logo/logo-icon.png" // Example: different logo for light/dark if needed
                  width={72}
                  height={72}
                  alt={tSidebar("PlatformSidebar.logoSmallAlt" as any)}
                  priority
                  className="dark:hidden"
                />
              )}
              {isOpen ? (
                <Image
                  src="/images/logo/logo-full-dark.png" // Example: different logo for light/dark if needed
                  width={130}
                  height={70} // Adjust to your logo's aspect ratio
                  alt={tSidebar("PlatformSidebar.logoAlt" as any)}
                  priority
                  className="hidden dark:block"
                />
              ) : (
                <Image
                  src="/images/logo/logo-icon.png" // Example: different logo for light/dark if needed
                  width={72}
                  height={72}
                  alt={tSidebar("PlatformSidebar.logoSmallAlt" as any)}
                  priority
                  className="hidden dark:block"
                />
              )}
            </motion.div>
          </AnimatePresence>
        </Link>
      </div>

      {/* Navigation Scroll Area */}
      <nav className="flex-1 overflow-y-auto px-3 py-2">
        {" "}
        {/* Add some padding */}
        {/* Optional Home/Dashboard Link */}
        {homeItem && renderMenuItem(homeItem, true)}
        {homeItem && (
          <hr className="dark:border-primary-dark-foreground/10 my-3 border-primary-foreground/10" />
        )}
        {sidebarSections.map((section, sectionIndex) => (
          <div
            key={section.titleKey}
            className={sectionIndex > 0 ? "mt-4" : ""}
          >
            <AnimatePresence>
              {isOpen && (
                <motion.h2
                  initial={{ opacity: 0, height: 0, y: -10 }}
                  animate={{
                    opacity: 1,
                    height: "auto",
                    y: 0,
                    transition: { delay: 0.1 },
                  }}
                  exit={{ opacity: 0, height: 0, y: -10 }}
                  className={cn(
                    "mb-2 px-1 text-xs font-semibold uppercase tracking-wider text-primary-foreground/60 dark:text-primary-dark-foreground/60"
                  )}
                >
                  {tSidebar(section.titleKey as any)}
                </motion.h2>
              )}
            </AnimatePresence>
            {!isOpen && sectionIndex > 0 && (
              <hr className="dark:border-primary-dark-foreground/10 my-3 border-primary-foreground/10" />
            )}

            <div className="space-y-1">
              {section.items.map((item) => renderMenuItem(item))}
            </div>
          </div>
        ))}
      </nav>

      {/* Optional: Footer section in sidebar e.g. User Profile quick link / Logout */}
      {/*
      <div className="dark:border-primary-dark-foreground/10 mt-auto border-t border-primary-foreground/10 p-3">
        {isOpen ? (
          // Expanded user info
        ) : (
          // Icon-only user avatar
        )}
      </div>
      */}
    </aside>
  );
};

export default PlatformSidebar;
