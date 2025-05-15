"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  UserPlusIcon,
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
import SignupModal from "@/components/auth/SignupModal";

const StudyPage = () => {
  const [isOpen, setIsOpen] = useState(true);
   const [showLogin, setShowLogin] = useState(false);
      const [showSignup, setShowSignup] = useState(false);
  
  
    const switchToLogin = () => {
      setShowSignup(false);
      setShowLogin(true);
    };
  
    // Function to switch from login to signup
    const switchToSignup = () => {
      setShowLogin(false);
      setShowSignup(true);
    };
  
    const openSignup = () => {
      setShowSignup(true);
      setShowLogin(false); // Close login if open
    };

  const menuItems = [
    { label: "تحديد المستوى", icon: <NewspaperIcon className="w-6 h-6" />, link: "/student/level" },
    { label: "التعلم بالطرق التقليدية", icon: <BookOpenIcon className="w-6 h-6" />, link: "/traditional-learning" },
    { label: "التعلم عبر المحادثة", icon: <ChatBubbleLeftRightIcon className="w-6 h-6" />, link: "/conversation-learning" },
    { label: "اختبارات المحاكاة", icon: <PencilSquareIcon className="w-6 h-6" />, link: "/simulation-tests" },
    { label: "المكافأت والمسابقات", icon: <GiftIcon className="w-6 h-6" />, link: "/rewards-and-competitions" },
    { label: "الاحصائيات", icon: <ChartPieIcon className="w-6 h-6" />, link: "/statistics" },
  ];

  const communityItems = [
    { label: "تحدى الزملاء", icon: <ClockIcon className="w-6 h-6" />, link: "/challenge-peers" },
    { label: "مجتمع الطلاب", icon: <UsersIcon className="w-6 h-6" />, link: "/student-community" },
    { label: "المدونة", icon: <BookmarkIcon className="w-6 h-6" />, link: "/blog" },
    { label: "الدعم الإدارى", icon: <QuestionMarkCircleIcon className="w-6 h-6" />, link: "/admin-support" },
  ];

  const settingsItems = [
    { label: "وضع الطوارئ", icon: <ExclamationCircleIcon className="w-6 h-6" />, link: "/emergency-mode" },
    { label: "الاعداد", icon: <Cog6ToothIcon className="w-6 h-6" />, link: "/settings" },
  ];

  return (
    <div className="flex min-h-screen dark:bg-[#081028] text-white">
      {/* Sidebar */}
      <div
        className="flex flex-col bg-[#074182] dark:bg-[#081028]  relative transition-all duration-300 ease-in-out border-l-[1px] border-gray-300"
        style={{ width: isOpen ? 220 : 100 }}
      >
        {/* زر الفتح/الإغلاق */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="absolute top-32 -left-3 bg-white text-[#074182] shadow-md rounded-md w-6 h-6 text-sm flex items-center justify-center z-50"
        >
          {isOpen ? ">" : "<"}
        </button>

        {/* الصورة + الاسم */}
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

        {/* Menu Sections */}
        <nav className="flex-1 mt-6 space-y-3 justify-center items-center">
          {/* تعلم Section */}
          <div>
            <p className={`text-white font-semibold mb-3 px-4 text-sm ${isOpen ? "text-start" : "text-center"} `}>التعلم</p>
            {menuItems.map((item, index) => (
              <Link key={index} href={item.link}>
                <motion.div
                  className={`flex items-center px-4 py-2 hover:bg-white/10 cursor-pointer transition-all duration-200 ${
                    isOpen ? "justify-start gap-3" : "justify-center"
                  }`}
                  whileHover={{ scale: 1.05 }}
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
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </motion.div>
              </Link>
            ))}
          </div>

          {/* مجتمع قادر Section */}
          <div>
            <p className="text-white font-semibold mb-3 px-4 text-sm">مجتمع قادر</p>
            {communityItems.map((item, index) => (
              <Link key={index} href={item.link}>
                <motion.div
                  className={`flex items-center px-4 py-2 hover:bg-white/10 cursor-pointer transition-all duration-200 ${
                    isOpen ? "justify-start gap-3" : "justify-center"
                  }`}
                  whileHover={{ scale: 1.05 }}
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
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </motion.div>
              </Link>
            ))}
          </div>

          {/* الإعدادات Section */}
          <div>
            <p className={`text-white font-semibold mb-3 px-4 text-sm ${isOpen ? "text-start" : "text-center"} `}>الإعدادات</p>
            {settingsItems.map((item, index) => (
              <Link key={index} href={item.link}>
                <motion.div
                  className={`flex items-center px-4 py-2 hover:bg-white/10 cursor-pointer transition-all duration-200 ${
                    isOpen ? "justify-start gap-3" : "justify-center"
                  }`}
                  whileHover={{ scale: 1.05 }}
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
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </motion.div>
              </Link>
            ))}
          </div>
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 flex items-center justify-center flex-col">
        <Image src={"/images/open-folder.png"} width={100} height={100} alt="" />
        <p className="font-semibold text-xl text-black dark:text-white">لا توجد ملفات لعرضها</p>
        <p className="text-gray-500 w-[180px] text-center dark:text-[#D9E1FA]">قم بإنشاء حساب لتستفيد من ميزات قادر</p>
        <button onClick={openSignup}  className="   flex justify-center gap-2 min-[1120px]:py-3 sm:w-[220px] w-[130px] mt-4  p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer">
          <UserPlusIcon className="w-5 h-5" />
          <span> اشتراك</span>
        </button>
      </div>

      <SignupModal
        show={showSignup}
        onClose={() => setShowSignup(false)}
        onSwitchToLogin={switchToLogin} // Pass switch handler
      />
    </div>
  );
};

export default StudyPage;
