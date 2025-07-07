import { ComponentType } from "react";
import {
  LayoutDashboard,
  Users,
  BarChart3,
  Settings,
  LucideProps,
  UserCheck,
  FileText,
  PanelTop,
  Handshake,
  MessageCircleQuestion,
  Mailbox,
  MessagesSquareIcon,
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
    titleKey: "AdminSidebar.sections.userManagement",
    items: [
      {
        labelKey: "AdminSidebar.items.employeesManagement",
        icon: Users,
        href: PATHS.ADMIN.EMPLOYEES_MANAGEMENT,
      },
      {
        labelKey: "AdminSidebar.items.studentsManagement",
        icon: UserCheck,
        href: PATHS.ADMIN.STUDENTS_MANAGEMENT,
      },
    ],
  },
  {
    titleKey: "AdminSidebar.sections.monitoring",
    items: [
      {
        labelKey: "AdminSidebar.items.statistics",
        icon: BarChart3,
        href: PATHS.ADMIN.STATISTICS_OVERVIEW,
      },
      {
        labelKey: "AdminSidebar.items.supportTickets",
        icon: MessagesSquareIcon,
        href: PATHS.ADMIN.SUPPORT_TICKETS,
      },
    ],
  },
  {
    titleKey: "AdminSidebar.sections.contentManagement",
    items: [
      {
        labelKey: "AdminSidebar.items.pages",
        icon: FileText,
        href: PATHS.ADMIN.CONTENT_PAGES_LIST,
      },
      {
        labelKey: "AdminSidebar.items.homepage",
        icon: PanelTop,
        href: PATHS.ADMIN.CONTENT_HOMEPAGE,
      },
      {
        labelKey: "AdminSidebar.items.partners",
        icon: Handshake,
        href: PATHS.ADMIN.CONTENT_PARTNERS,
      },
      {
        labelKey: "AdminSidebar.items.faqs",
        icon: MessageCircleQuestion,
        href: PATHS.ADMIN.CONTENT_FAQS,
      },
      {
        labelKey: "AdminSidebar.items.contactMessages",
        icon: Mailbox,
        href: PATHS.ADMIN.CONTENT_CONTACT_MESSAGES,
      },
    ],
  },
  // {
  //   titleKey: "AdminSidebar.sections.system",
  //   items: [
  //     {
  //       labelKey: "AdminSidebar.items.settings",
  //       icon: Settings,
  //       href: PATHS.ADMIN.SETTINGS,
  //     },
  //   ],
  // },
];
