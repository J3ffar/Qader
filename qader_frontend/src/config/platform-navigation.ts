import { ComponentType, SVGProps } from "react";

// Import Lucide React icons
import {
  Home,
  BookOpenText,
  Newspaper,
  MessageSquareText,
  FilePenLine,
  Gift,
  PieChart,
  Timer,
  Users,
  Bookmark,
  HelpCircle,
  ShieldAlert,
  Settings,
  LucideProps,
  // Added for new "coming soon" links
  Compass,
  User,
  UsersRound,
  Presentation,
} from "lucide-react";

import { PATHS } from "@/constants/paths";

// More specific translation key type for clarity
export type PlatformSidebarTranslationKey =
  | `PlatformSidebar.sections.${string}`
  | `PlatformSidebar.items.${string}`
  | `PlatformSidebar.toggleOpen`
  | `PlatformSidebar.toggleClose`
  | `PlatformSidebar.logoAlt`
  | `PlatformSidebar.logoSmallAlt`;

// Using LucideProps for the icon type for better compatibility with Lucide
export interface PlatformSidebarNavItem {
  labelKey: PlatformSidebarTranslationKey;
  icon: ComponentType<LucideProps>; // Changed SVGProps to LucideProps
  href: string;
  exactMatch?: boolean;
  disabled?: boolean;
  comingSoon?: boolean;
}

export interface PlatformSidebarNavSection {
  titleKey: PlatformSidebarTranslationKey;
  items: PlatformSidebarNavItem[];
}

export const PLATFORM_SIDEBAR_SECTIONS: PlatformSidebarNavSection[] = [
  {
    titleKey: "PlatformSidebar.sections.learning",
    items: [
      {
        labelKey: "PlatformSidebar.items.determineLevel",
        icon: Newspaper,
        href: PATHS.STUDY.DETERMINE_LEVEL.LIST,
      },
      {
        labelKey: "PlatformSidebar.items.traditionalLearning",
        icon: BookOpenText,
        href: PATHS.STUDY.TRADITIONAL_LEARNING.LIST,
      },
      {
        labelKey: "PlatformSidebar.items.emergencyMode",
        icon: ShieldAlert,
        href: PATHS.STUDY.EMERGENCY_MODE,
      },
      {
        labelKey: "PlatformSidebar.items.conversationalLearning",
        icon: MessageSquareText,
        href: PATHS.STUDY.CONVERSATIONAL_LEARNING.HOME,
      },
      {
        labelKey: "PlatformSidebar.items.tests",
        icon: FilePenLine,
        href: PATHS.STUDY.TESTS.LIST,
      },
      {
        labelKey: "PlatformSidebar.items.statistics",
        icon: PieChart,
        href: PATHS.STUDY.STATISTICS,
      },
    ],
  },
  {
    titleKey: "PlatformSidebar.sections.engagement",
    items: [
      {
        labelKey: "PlatformSidebar.items.blog",
        icon: Bookmark,
        href: PATHS.STUDY.BLOG.HOME,
      },
      {
        labelKey: "PlatformSidebar.items.rewards",
        icon: Gift,
        href: PATHS.STUDY.REWARDS_AND_COMPETITIONS,
      },
      {
        labelKey: "PlatformSidebar.items.challengeColleagues",
        icon: Timer,
        href: PATHS.STUDY.CHALLENGE_COLLEAGUES,
      },
      {
        labelKey: "PlatformSidebar.items.community",
        icon: Users,
        href: PATHS.STUDY.STUDY_COMMUNITY,
      },
      {
        labelKey: "PlatformSidebar.items.explore",
        icon: Compass,
        href: "#",
        comingSoon: true,
      },
      {
        labelKey: "PlatformSidebar.items.studyGroups",
        icon: UsersRound,
        href: "#",
        comingSoon: true,
      },
      {
        labelKey: "PlatformSidebar.items.studyRooms",
        icon: Presentation,
        href: "#",
        comingSoon: true,
      },
    ],
  },
  {
    titleKey: "PlatformSidebar.sections.account",
    items: [
      {
        labelKey: "PlatformSidebar.items.profile",
        icon: User,
        href: "#",
        comingSoon: true,
      },
      {
        labelKey: "PlatformSidebar.items.settings",
        icon: Settings,
        href: PATHS.STUDY.SETTINGS.HOME,
      },
      {
        labelKey: "PlatformSidebar.items.adminSupport",
        icon: HelpCircle,
        href: PATHS.STUDY.ADMIN_SUPPORT,
      },
    ],
  },
];

export const PLATFORM_SIDEBAR_HOME_ITEM: PlatformSidebarNavItem = {
  labelKey: "PlatformSidebar.items.studyDashboard",
  icon: Home,
  href: PATHS.STUDY.HOME,
  exactMatch: true,
};
