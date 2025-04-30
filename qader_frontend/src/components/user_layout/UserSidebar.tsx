"use client";

import { useState } from "react";
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

  const menuItems = [
    {
      label: "تحديد المستوى",
      icon: <NewspaperIcon className="w-6 h-6" />,
      link: "/student/level",
    },
    {
      label: "التعلم بالطرق التقليدية",
      icon: <BookOpenIcon className="w-6 h-6" />,
      link: "/user/traditional-learning",
    },
    {
      label: "التعلم عبر المحادثة",
      icon: <ChatBubbleLeftRightIcon className="w-6 h-6" />,
      link: "/user/conversation-learning",
    },
    {
      label: "اختبارات المحاكاة",
      icon: <PencilSquareIcon className="w-6 h-6" />,
      link: "/user/simulation-tests",
    },
    {
      label: "المكافأت والمسابقات",
      icon: <GiftIcon className="w-6 h-6" />,
      link: "/user/rewards-and-competitions",
    },
    {
      label: "الاحصائيات",
      icon: <ChartPieIcon className="w-6 h-6" />,
      link: "/user/statistics",
    },
  ];

  const communityItems = [
    {
      label: "تحدى الزملاء",
      icon: <ClockIcon className="w-6 h-6" />,
      link: "/user/challenge-peers",
    },
    {
      label: "مجتمع الطلاب",
      icon: <UsersIcon className="w-6 h-6" />,
      link: "/user/student-community",
    },
    {
      label: "المدونة",
      icon: <BookmarkIcon className="w-6 h-6" />,
      link: "/user/blog",
    },
    {
      label: "الدعم الإدارى",
      icon: <QuestionMarkCircleIcon className="w-6 h-6" />,
      link: "/user/admin-support",
    },
  ];

  const settingsItems = [
    {
      label: "وضع الطوارئ",
      icon: <ExclamationCircleIcon className="w-6 h-6" />,
      link: "/user/emergency-mode",
    },
    {
      label: "الإعدادات",
      icon: <Cog6ToothIcon className="w-6 h-6" />,
      link: "/user/settings",
    },
  ];

  const renderMenu = (
    items: { label: string; icon: JSX.Element; link: string }[]
  ) => {
    return items.map((item, index) => {
      const isActive = pathname === item.link;

      return (
        <Link key={index} href={item.link}>
          <motion.div
            className={`flex items-center gap-3 px-4 py-2 cursor-pointer 
              transition-all duration-200
              ${isActive ? "bg-white/20" : "hover:bg-white/10"}
            `}
            whileHover={{ scale: 1.05 }}
            animate={isActive ? { scale: 1.05 } : {}}
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
                  className={isActive ? "font-bold" : ""}
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

  return (
    <div
      className="flex relative flex-col bg-[#074182] min-h-screen text-white transition-all duration-300 ease-in-out z-50"
      style={{ width: isOpen ? 220 : 70 }}
    >
      {/* زرار الفتح والغلق */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="absolute cursor-pointer top-32 -left-3 bg-white text-[#074182] shadow-md rounded-md w-6 h-6 text-sm flex items-center justify-center"
      >
        {isOpen ? ">" : "<"}
      </button>

      {/* صورة المستخدم */}
      <div className="flex flex-col items-center py-6 border-b border-white/20">
        <div className="w-16 h-16 rounded-full overflow-hidden mb-2">
          <Image
            src="/images/signup.png"
            width={64}
            height={64}
            alt=""
            className="object-cover w-full h-full"
          />
        </div>
        <AnimatePresence>
          {isOpen && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-sm font-semibold"
            >
              زائر
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* القوائم */}
      <nav className="flex-1 mt-6 space-y-3">
        <div>
          <p className="text-white font-semibold mb-3 px-4">التعلم</p>
          {renderMenu(menuItems)}
        </div>

        <div>
          <p className="text-white font-semibold mb-3 px-4">مجتمع قادر</p>
          {renderMenu(communityItems)}
        </div>

        <div>
          <p className="text-white font-semibold mb-3 px-4">الإعدادات</p>
          {renderMenu(settingsItems)}
        </div>
      </nav>
    </div>
  );
};

export default Sidebar;
