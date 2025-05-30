// qader_frontend/src/components/user_layout/UserSidebar.tsx
"use client";

import { useState, useEffect, useMemo } from "react";
import { usePathname } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import { ChevronLeftIcon, ChevronRightIcon } from "@heroicons/react/24/solid"; // For toggle

import { cn } from "@/lib/utils";
import {
  SIDEBAR_SECTIONS,
  SidebarNavItem,
} from "@/constants/sidebar-navigation"; // Adjust path
import { PATHS } from "@/constants/paths";

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: (value: boolean) => void;
}

const UserSidebar = ({ isOpen, setIsOpen }: SidebarProps) => {
  const t = useTranslations();
  const pathname = usePathname();
  const locale = useLocale();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const sidebarSections = useMemo(() => SIDEBAR_SECTIONS, []);

  if (!isClient) {
    return null;
  }

  const ToggleIcon = () => {
    // Using Heroicons for toggle
    const Icon = isOpen
      ? locale === "ar"
        ? ChevronRightIcon
        : ChevronLeftIcon
      : locale === "ar"
      ? ChevronLeftIcon
      : ChevronRightIcon;
    return <Icon className="h-4 w-4" />;
  };

  const renderMenuItem = (item: SidebarNavItem) => {
    const isActive = item.exactMatch
      ? pathname === item.href
      : pathname.startsWith(item.href);

    const IconComponent = item.icon;

    return (
      <Link key={item.labelKey} href={item.href} passHref legacyBehavior>
        <motion.a
          className={cn(
            "flex items-center px-4 py-2 cursor-pointer transition-all duration-200 text-white", // py-2 as original
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-[#074182] dark:focus-visible:ring-offset-[#081028]",
            isOpen ? "justify-start gap-x-3" : "justify-center",
            isActive ? "bg-white/20" : "hover:bg-white/10"
          )}
          whileHover={{ scale: 1.05 }} // Kept from original logic
          animate={isActive ? { scale: 1.05 } : {}} // Kept from original logic
          transition={{ duration: 0.2 }}
          aria-current={isActive ? "page" : undefined}
        >
          {/* Icon size h-6 w-6 as original */}
          <IconComponent
            className={cn("h-6 w-6", isOpen ? "me-0" : "mx-auto")}
          />
          <AnimatePresence>
            {isOpen && (
              <motion.span
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.15 }}
                className={cn("whitespace-nowrap", isActive ? "font-bold" : "")} // font-bold for active text
              >
                {t(item.labelKey as any)}
              </motion.span>
            )}
          </AnimatePresence>
        </motion.a>
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        "relative z-40 flex min-h-screen flex-col text-white transition-all duration-300 ease-in-out",
        "bg-[#074182] dark:bg-[#081028]", // Original colors
        isOpen ? "w-[220px]" : "w-[100px]" // Original dimensions
      )}
      aria-label={t("Nav.UserSideBar.sections.learning")} // Or a more generic sidebar label
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "absolute top-32 z-50 flex h-7 w-7 cursor-pointer items-center justify-center rounded-md border shadow-md",
          "bg-white text-[#074182] dark:bg-transparent dark:text-white dark:border-neutral-600", // Original toggle colors
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#074182] dark:focus-visible:ring-white focus-visible:ring-offset-1",
          // Original positioning:
          // If sidebar is on the left (default LTR), button is to its right.
          // If sidebar is on the right (RTL), button is to its left.
          // The original "-left-3" suggests the button was on the left edge OF the sidebar, pushing out.
          // This needs to be adjusted based on whether the sidebar itself is positioned left/right.
          // Assuming sidebar is always on the "start" edge (left in LTR, right in RTL):
          isOpen
            ? "ltr:left-[calc(220px-12px)] rtl:right-[calc(220px-12px)] transform ltr:-translate-x-0 rtl:translate-x-0"
            : "ltr:left-[calc(100px-12px)] rtl:right-[calc(100px-12px)] transform ltr:-translate-x-0 rtl:translate-x-0",
          // The above places it *on* the sidebar near the outer edge.
          // If original `-left-3` meant relative to viewport when sidebar is right-aligned:
          // Let's try to replicate original `-left-3 top-32` which means it was always on the left of the sidebar.
          // This implies the sidebar itself might have been on the right, or the button was meant to be on the viewport's left edge.
          // For simplicity and common pattern, placing it on the *outer edge* of the sidebar:
          "top-30 -translate-y-1/2", // Centered vertically
          "ltr:-right-3 rtl:-left-3 transition-all" // Original intention seems to be this relative to sidebar body
        )}
        aria-label={
          isOpen
            ? t("Nav.UserSideBar.toggleClose")
            : t("Nav.UserSideBar.toggleOpen")
        }
        aria-expanded={isOpen}
      >
        {/* Original toggle button text: */}
        {/* {isOpen ? (locale === 'ar' ? "<" : ">") : (locale === 'ar' ? ">" : "<")} */}
        {/* Using icons as it's generally better: */}
        <ToggleIcon />
      </button>

      <div className="flex flex-col items-center py-6">
        {" "}
        {/* Original padding py-6 */}
        <Link
          href={PATHS.STUDY.HOME}
          className="mb-2 block rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white"
        >
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={isOpen ? "logo-large" : "logo-small"}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.2 }}
              className="flex items-center justify-center"
            >
              {isOpen ? (
                <Image
                  src="/images/logosidebar.png"
                  width={120} // Original width
                  height={120} // Original height (assuming square, adjust if not)
                  alt={t("qaderLogoAlt")}
                  priority
                />
              ) : (
                <Image
                  src="/images/logoside.png"
                  width={71} // Original width
                  height={71} // Original height
                  alt={t("Nav.qaderLogoAlt")}
                  priority
                />
              )}
            </motion.div>
          </AnimatePresence>
        </Link>
      </div>

      <nav className="flex-1 space-y-3 px-2">
        {" "}
        {/* Original mt-6, space-y-3. Added px-2 for overall padding if items don't have it fully */}
        {sidebarSections.map((section) => (
          <div key={section.titleKey}>
            {/* Original title styling */}
            <motion.h2
              // Animate only if isOpen to prevent layout shift or if you prefer it always visible
              initial={
                isOpen
                  ? { opacity: 0, x: locale === "ar" ? 10 : -10 }
                  : { opacity: 1, x: 0 }
              }
              animate={
                isOpen
                  ? { opacity: 1, x: 0 }
                  : {
                      opacity:
                        !isOpen &&
                        section.items.some((item) =>
                          pathname.startsWith(item.href)
                        )
                          ? 0
                          : 1,
                      height: !isOpen ? "0px" : "auto",
                    }
              } // Hide if not open, unless an item is active
              transition={{ duration: 0.2, delay: isOpen ? 0.1 : 0 }}
              className={cn(
                "text-white font-semibold mb-4 text-xl", // Original style
                isOpen ? "px-4 text-start" : "text-center", // Text alignment based on locale
                !isOpen && "sr-only" // Hide visually when closed, but accessible
              )}
            >
              {t(section.titleKey as any)}
            </motion.h2>

            {/* Divider for closed state - optional */}
            {!isOpen && sidebarSections.indexOf(section) > 0 && (
              <hr className="my-3 border-white/10" />
            )}

            <div className={cn("space-y-1", !isOpen && "mt-2")}>
              {section.items.map(renderMenuItem)}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
};

export default UserSidebar;
