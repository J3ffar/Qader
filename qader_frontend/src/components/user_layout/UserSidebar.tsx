"use client";

import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import Link from "next/link";
import {
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
import { JSX } from "react/jsx-runtime";

interface SidebarProps {
  isOpen: boolean;
  setIsOpen: (value: boolean) => void;
}

const Sidebar = ({ isOpen, setIsOpen }: SidebarProps) => {
  const pathname = usePathname();
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) return null;

  const menuItems = [
    {
      label: "تحديد المستوى",
      icon: <NewspaperIcon className="h-6 w-6" />,
      link: "/study/determine-level",
      subLink: "/study/determine-level/pic",
    },
    {
      label: "التعلم بالطرق التقليدية",
      icon: <BookOpenIcon className="h-6 w-6" />,
      link: "/study/traditional-learning",
      subLink: "",
    },
    {
      label: "التعلم عبر المحادثة",
      icon: <ChatBubbleLeftRightIcon className="h-6 w-6" />,
      link: "/study/conversation-learning",
      subLink: "",
    },
    {
      label: "اختبارات المحاكاة",
      icon: <PencilSquareIcon className="h-6 w-6" />,
      link: "/study/simulation-tests",
      subLink: "",
    },
    {
      label: "المكافأت والمسابقات",
      icon: <GiftIcon className="h-6 w-6" />,
      link: "/study/rewards-and-competitions",
      subLink: "",
    },
    {
      label: "الاحصائيات",
      icon: <ChartPieIcon className="h-6 w-6" />,
      link: "/study/statistics",
      subLink: "",
    },
  ];

  const communityItems = [
    {
      label: "تحدى الزملاء",
      icon: <ClockIcon className="h-6 w-6" />,
      link: "/study/challenge-peers",
      subLink: "",
    },
    {
      label: "مجتمع الطلاب",
      icon: <UsersIcon className="h-6 w-6" />,
      link: "/study/study-community",
      subLink: "",
    },
    {
      label: "المدونة",
      icon: <BookmarkIcon className="h-6 w-6" />,
      link: "/study/blog",
      subLink: "",
    },
    {
      label: "الدعم الإدارى",
      icon: <QuestionMarkCircleIcon className="h-6 w-6" />,
      link: "/study/admin-support",
      subLink: "",
    },
  ];

  const settingsItems = [
    {
      label: "وضع الطوارئ",
      icon: <ExclamationCircleIcon className="h-6 w-6" />,
      link: "/study/emergency-mode",
      subLink: "",
    },
    {
      label: "الإعدادات",
      icon: <Cog6ToothIcon className="h-6 w-6" />,
      link: "/study/settings",
      subLink: "",
    },
  ];

  const renderMenu = (
    items: { label: string; icon: JSX.Element; link: string; subLink: string }[]
  ) => {
    return items.map((item, index) => {
      const isActive = pathname === item.link;
      const isActives = pathname === item.subLink;

      return (
        <Link key={index} href={item.link}>
          <motion.div
            className={`flex items-center px-4 py-2 cursor-pointer transition-all duration-200 
              ${isOpen ? "justify-start gap-3" : "justify-center"}
              ${isActive || isActives ? "bg-white/20" : "hover:bg-white/10"}
            `}
            whileHover={{ scale: 1.05 }}
            animate={isActive || isActives ? { scale: 1.05 } : {}}
            transition={{ duration: 0.2 }}
          >
            {item.icon}
            <AnimatePresence>
              {isOpen && (
                <motion.span
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  transition={{ duration: 0.2 }}
                  className={isActive || isActives ? "font-bold" : ""}
                >
                  {item.label}
                </motion.span>
              )}
            </AnimatePresence>
          </motion.div>
        </Link>
      );
    });
  };

  const renderTitle = (title: string) => {
    return (
      <div
        className={`text-white font-semibold mb-3 text-sm ${
          isOpen ? "px-4 text-right" : "text-center"
        }`}
      >
        {title}
      </div>
    );
  };

  return (
    <div
      className="relative z-50 flex min-h-screen flex-col bg-[#074182] text-white transition-all duration-300 ease-in-out dark:bg-[#081028]"
      style={{ width: isOpen ? 220 : 100 }}
    >
      {/* زر الفتح/الإغلاق */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="absolute -left-3 top-32 flex h-6 w-6 cursor-pointer items-center justify-center rounded-md border bg-white text-sm text-[#074182] shadow-md dark:bg-transparent dark:text-white"
      >
        {isOpen ? ">" : "<"}
      </button>

      {/* صورة المستخدم */}
      <div className="flex flex-col items-center py-6">
        <div className="mb-2 flex items-center justify-center">
          {isOpen ? (
            <Image
              src="/images/logosidebar.png"
              width={120}
              height={120}
              alt=""
            />
          ) : (
            <Image src="/images/logoside.png" width={71} height={71} alt="" />
          )}
        </div>
      </div>

      {/* القوائم */}
      <nav className="mt-6 flex-1 space-y-3">
        <div>
          {renderTitle("التعلم")}
          {renderMenu(menuItems)}
        </div>

        <div>
          {renderTitle("مجتمع قادر")}
          {renderMenu(communityItems)}
        </div>

        <div>
          {renderTitle("الإعدادات")}
          {renderMenu(settingsItems)}
        </div>
      </nav>
    </div>
  );
};

export default Sidebar;
