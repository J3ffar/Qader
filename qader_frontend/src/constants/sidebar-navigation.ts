import { ComponentType, SVGProps } from "react";
import {
  HomeIcon, // Assuming HomeIcon exists in Heroicons outline or use a similar one
  BookOpenIcon,
  NewspaperIcon,
  ChatBubbleLeftRightIcon,
  PencilSquareIcon,
  GiftIcon,
  ChartPieIcon,
  ClockIcon,
  UsersIcon,
  BookmarkIcon,
  QuestionMarkCircleIcon,
  ExclamationCircleIcon,
  Cog6ToothIcon,
} from "@heroicons/react/24/outline";
import { PATHS } from "./paths";

// Ensure UserSidebarTranslationKey matches the structure in your nav.json
// For simplicity, using a template literal type that's broad.
// Refine this if you have a very strict/generated type for your translation keys.
export type UserSidebarTranslationKey =
  | `Nav.UserSideBar.sections.${string}`
  | `Nav.UserSideBar.study.${string}`
  | `Nav.UserSideBar.toggleOpen`
  | `Nav.UserSideBar.toggleClose`;

export interface SidebarNavItem {
  labelKey: UserSidebarTranslationKey;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  href: string;
  /** If true, path must be an exact match. Otherwise, startsWith is used. */
  exactMatch?: boolean;
}

export interface SidebarNavSection {
  titleKey: UserSidebarTranslationKey;
  items: SidebarNavItem[];
}

export const SIDEBAR_SECTIONS: SidebarNavSection[] = [
  {
    titleKey: "Nav.UserSideBar.sections.learning",
    items: [
      {
        labelKey: "Nav.UserSideBar.study.home",
        icon: HomeIcon, // Changed from Lucide Home
        href: PATHS.STUDY.HOME,
        exactMatch: true,
      },
      {
        labelKey: "Nav.UserSideBar.study.determine-level",
        icon: NewspaperIcon,
        href: PATHS.STUDY.DETERMINE_LEVEL.LIST,
      },
      {
        labelKey: "Nav.UserSideBar.study.traditional-learning",
        icon: BookOpenIcon,
        href: PATHS.STUDY.TRADITIONAL_LEARNING.HOME,
      },
      {
        labelKey: "Nav.UserSideBar.study.conversational-learning",
        icon: ChatBubbleLeftRightIcon,
        href: PATHS.STUDY.CONVERSATIONAL_LEARNING.HOME,
      },
      {
        labelKey: "Nav.UserSideBar.study.tests", // "Simulation Tests"
        icon: PencilSquareIcon,
        href: PATHS.STUDY.SIMULATION_TESTS.HOME,
      },
      {
        labelKey: "Nav.UserSideBar.study.rewards-and-competitions",
        icon: GiftIcon,
        href: PATHS.STUDY.REWARDS_AND_COMPETITIONS,
      },
      {
        labelKey: "Nav.UserSideBar.study.statistics",
        icon: ChartPieIcon,
        href: PATHS.STUDY.STATISTICS,
      },
    ],
  },
  {
    titleKey: "Nav.UserSideBar.sections.community",
    items: [
      {
        labelKey: "Nav.UserSideBar.study.challenge-colleagues",
        icon: ClockIcon, // Or UsersIcon, BeakerIcon, etc. for "challenge"
        href: PATHS.STUDY.CHALLENGE_COLLEAGUES,
      },
      {
        labelKey: "Nav.UserSideBar.study.community",
        icon: UsersIcon,
        href: PATHS.STUDY.STUDY_COMMUNITY,
      },
      {
        labelKey: "Nav.UserSideBar.study.blog",
        icon: BookmarkIcon, // Or DocumentTextIcon for "blog"
        href: PATHS.STUDY.BLOG.HOME,
      },
      {
        labelKey: "Nav.UserSideBar.study.admin-support",
        icon: QuestionMarkCircleIcon,
        href: PATHS.STUDY.ADMIN_SUPPORT,
      },
    ],
  },
  {
    titleKey: "Nav.UserSideBar.sections.settings",
    items: [
      {
        labelKey: "Nav.UserSideBar.study.emergency-mode",
        icon: ExclamationCircleIcon,
        href: PATHS.STUDY.EMERGENCY_MODE,
      },
      {
        labelKey: "Nav.UserSideBar.study.settings",
        icon: Cog6ToothIcon,
        href: PATHS.SETTINGS.HOME,
      },
    ],
  },
];
