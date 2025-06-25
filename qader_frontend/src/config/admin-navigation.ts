import { ComponentType } from "react";
import {
  LayoutDashboard,
  Users,
  FolderKanban,
  BarChart3,
  MessageSquareQuote,
  Settings,
  LucideProps,
} from "lucide-react";

import { PATHS } from "@/constants/paths";

// Using a more specific type for admin translations for clarity
export type AdminSidebarTranslationKey =
  | `AdminSidebar.sections.${string}`
  | `AdminSidebar.items.${string}`
  | `AdminSidebar.toggleOpen`
  | `AdminSidebar.toggleClose`
  | `AdminSidebar.logoAlt`
  | `AdminSidebar.logoSmallAlt`;

export interface AdminSidebarNavItem {
  labelKey: AdminSidebarTranslationKey;
  icon: ComponentType<LucideProps>;
  href: string;
  exactMatch?: boolean;
}

export interface AdminSidebarNavSection {
  titleKey: AdminSidebarTranslationKey;
  items: AdminSidebarNavItem[];
}

// Define the home/dashboard item separately
export const ADMIN_SIDEBAR_HOME_ITEM: AdminSidebarNavItem = {
  labelKey: "AdminSidebar.items.dashboard",
  icon: LayoutDashboard,
  href: PATHS.ADMIN.DASHBOARD,
  exactMatch: true,
};

// Define the main sections and their items
export const ADMIN_SIDEBAR_SECTIONS: AdminSidebarNavSection[] = [
  {
    titleKey: "AdminSidebar.sections.management",
    items: [
      {
        labelKey: "AdminSidebar.items.employeesManagement",
        icon: Users,
        href: PATHS.ADMIN.EMPLOYEES_MANAGEMENT,
      },
      {
        labelKey: "AdminSidebar.items.studentsManagement",
        icon: Users,
        href: PATHS.ADMIN.STUDENTS_MANAGEMENT,
      },
      {
        labelKey: "AdminSidebar.items.pageManagement",
        icon: FolderKanban,
        href: PATHS.ADMIN.PAGES_MANAGEMENT,
      },
    ],
  },
  {
    titleKey: "AdminSidebar.sections.monitoring",
    items: [
      {
        labelKey: "AdminSidebar.items.statistics",
        icon: BarChart3,
        href: PATHS.ADMIN.ANALYTICS,
      },
      {
        labelKey: "AdminSidebar.items.contentTickets",
        icon: MessageSquareQuote,
        href: PATHS.ADMIN.SUPPORT_TICKETS,
      },
    ],
  },
  //   {
  //     titleKey: "AdminSidebar.sections.system",
  //     items: [
  //       {
  //         labelKey: "AdminSidebar.items.settings",
  //         icon: Settings,
  //         href: PATHS.ADMIN.SETTINGS,
  //       },
  //     ],
  //   },
];
