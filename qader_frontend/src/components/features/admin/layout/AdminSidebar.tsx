// src/components/features/admin/layout/AdminSidebar.tsx
"use client";

import { useState, useEffect, useMemo } from "react";
import { usePathname } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import { PanelLeftClose, PanelRightClose } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  ADMIN_SIDEBAR_SECTIONS,
  ADMIN_SIDEBAR_HOME_ITEM,
  AdminSidebarNavItem,
} from "@/config/admin-navigation";
import { PATHS } from "@/constants/paths";
import { Skeleton } from "@/components/ui/skeleton";

interface AdminSidebarProps {
  isOpen: boolean;
  setIsOpen: (value: boolean) => void;
}

const AdminSidebar = ({ isOpen, setIsOpen }: AdminSidebarProps) => {
  const t = useTranslations("Nav"); // Assuming admin keys are in 'Nav.json'
  const pathname = usePathname();
  const locale = useLocale();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const sidebarSections = useMemo(() => ADMIN_SIDEBAR_SECTIONS, []);
  // const homeItem = useMemo(() => ADMIN_SIDEBAR_HOME_ITEM, []);

  if (!isClient) {
    return <AdminSidebarSkeleton />;
  }

  const ToggleIcon = isOpen
    ? locale === "ar"
      ? PanelRightClose
      : PanelLeftClose
    : locale === "ar"
    ? PanelLeftClose
    : PanelRightClose;

  const renderMenuItem = (item: AdminSidebarNavItem) => {
    const isActive = item.exactMatch
      ? pathname === item.href
      : pathname.startsWith(item.href);
    const IconComponent = item.icon;

    return (
      <Link
        key={item.href}
        href={item.href}
        aria-current={isActive ? "page" : undefined}
      >
        <motion.div
          className={cn(
            "flex items-center mb-2 rounded-md px-3 py-2.5 text-sm transition-colors duration-150",
            isOpen ? "justify-start gap-x-3" : "justify-center",
            isActive
              ? "bg-primary text-primary-foreground" // Active state stands out
              : "text-slate-700 dark:text-slate-300 hover:bg-primary hover:text-white"
          )}
          whileHover={!isActive ? { scale: 1.03 } : {}}
          transition={{ duration: 0.15 }}
        >
          <IconComponent className="h-5 w-5 flex-shrink-0" />
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
                {t(item.labelKey as any)}
              </motion.span>
            )}
          </AnimatePresence>
        </motion.div>
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        "sticky top-0 z-50 flex h-screen flex-col bg-background text-white transition-all duration-300 ease-in-out border-l border-border",
        isOpen ? "w-60" : "w-[72px]"
      )}
      aria-label={t("AdminSidebar.sidebarNavigationLabel" as any)}
    >
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "absolute top-15 z-50 flex h-8 w-8 items-center justify-center rounded-full border border-border bg-muted text-muted-foreground shadow-md transition-all hover:bg-muted/80",
          isOpen
            ? locale === "ar"
              ? "-left-3.5"
              : "-right-3.5"
            : "ltr:right-[-14px] rtl:left-[-14px]"
        )}
        aria-label={t(
          isOpen
            ? "AdminSidebar.toggleClose"
            : ("AdminSidebar.toggleOpen" as any)
        )}
        aria-expanded={isOpen}
      >
        <ToggleIcon className="h-5 w-5" />
      </button>

      <div
        className={cn(
          "flex h-[var(--header-height,80px)] items-center justify-center border-b border-border",
          isOpen ? "px-6" : "px-3"
        )}
      >
        <Link href={`/${locale}${PATHS.ADMIN.DASHBOARD}`}>
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={isOpen ? "logo-large" : "logo-small"}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.2 }}
            >
              {isOpen ? (
                <Image
                  src="/images/logo.svg"
                  width={130}
                  height={70}
                  alt={t("AdminSidebar.logoAlt" as any)}
                  priority
                />
              ) : (
                <Image
                  src="/images/logo/logo-icon.png"
                  width={40}
                  height={40}
                  alt={t("AdminSidebar.logoSmallAlt" as any)}
                  priority
                />
              )}
            </motion.div>
          </AnimatePresence>
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {/* {renderMenuItem(homeItem)}
        <hr className="my-3 border-slate-700" /> */}

        {sidebarSections.map((section, sectionIndex) => (
          <div
            key={section.titleKey}
            className={sectionIndex > 0 ? "mt-4" : ""}
          >
            <AnimatePresence>
              {isOpen && (
                <motion.h2
                  initial={{ opacity: 0, height: 0 }}
                  animate={{
                    opacity: 1,
                    height: "auto",
                    transition: { delay: 0.1 },
                  }}
                  exit={{ opacity: 0, height: 0 }}
                  className="mb-2 px-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground"
                >
                  {t(section.titleKey as any)}
                </motion.h2>
              )}
            </AnimatePresence>
            {!isOpen && sectionIndex > 0 && (
              <hr className="my-3 border-slate-700" />
            )}
            <div className="space-y-1">
              {section.items.map((item) => renderMenuItem(item))}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  );
};

const AdminSidebarSkeleton = () => (
  <aside className="sticky top-0 z-50 flex h-screen w-[72px] flex-col bg-background shadow-lg md:w-60">
    <div className="flex h-[80px] items-center justify-center border-b border-border">
      <Skeleton className="h-[40px] w-[40px] rounded-md md:h-[50px] md:w-[120px]" />
    </div>
    <div className="flex-1 space-y-3 px-3 py-4">
      {[...Array(3)].map((_, sectionIndex) => (
        <div key={sectionIndex}>
          <Skeleton className="mb-4 hidden h-5 w-3/4 md:block" />
          {[...Array(2)].map((_, itemIndex) => (
            <div
              key={itemIndex}
              className="flex items-center justify-center gap-x-3 py-3 md:justify-start"
            >
              <Skeleton className="h-6 w-6 rounded" />
              <Skeleton className="hidden h-5 w-24 md:block" />
            </div>
          ))}
        </div>
      ))}
    </div>
  </aside>
);

export default AdminSidebar;
