"use client";
import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import LoginModal from "@/components/auth/LoginModal";
import SignupModal from "@/components/auth/SignupModal";
import {
  Bars3Icon,
  XMarkIcon,
  UserIcon,
  UserPlusIcon,
  HomeIcon,
  BookOpenIcon,
  PencilIcon,
  UsersIcon,
  QuestionMarkCircleIcon,
  ChatBubbleOvalLeftEllipsisIcon,
} from "@heroicons/react/24/solid";
import { useTheme } from "next-themes";

const navLinks = [
  { name: "الرئيسية", ref: "/", icon: HomeIcon },
  { name: "قصتنا", ref: "/about", icon: BookOpenIcon },
  { name: "شركاء النجاح", ref: "/partners", icon: UsersIcon },
  { name: "صفحة المذاكرة", ref: "/study", icon: PencilIcon },
  { name: "الأسئلة الشائعة", ref: "/questions", icon: QuestionMarkCircleIcon },
  { name: "تواصل معنا", ref: "/contact", icon: ChatBubbleOvalLeftEllipsisIcon },
];

const Navbar = () => {
  const [showNav, setShowNav] = useState(false);
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  const pathname = usePathname();

  const { theme, setTheme } = useTheme();



  const isDark = theme === "dark";

  const handleNav = () => setShowNav(!showNav);
  const closeNav = () => setShowNav(false);

  // Functions to open modals and close the other one
  const openLogin = () => {
    setShowLogin(true);
    setShowSignup(false); // Close signup if open
    closeNav(); // Close mobile nav if open
  };
  const openSignup = () => {
    setShowSignup(true);
    setShowLogin(false); // Close login if open
    closeNav(); // Close mobile nav if open
  };

  // Function to switch from signup to login
  const switchToLogin = () => {
    setShowSignup(false);
    setShowLogin(true);
  };

  // Function to switch from login to signup
  const switchToSignup = () => {
    setShowLogin(false);
    setShowSignup(true);
  };

  return (
    <>
      <div className="relative z-50">
        <nav className="flex justify-between items-center shadow-lg px-4 sm:px-8 md:px-16 py-4 w-full bg-background max-md:bg-[#074182] dark:max-md:bg-[#081028] md:bg-[#FDFDFD] dark:md:bg-[#081028] max-md:flex-row-reverse max-md:gap-6">
          {/* Hamburger Icon 'we will back to her later' */}
          <div className="hidden max-md:flex">
            <button
              onClick={handleNav}
              aria-label={showNav ? "Close menu" : "Open menu"}
            >
              {showNav ? (
                <XMarkIcon className="w-8 h-8 max-md:text-white" />
              ) : (
                <Bars3Icon className="w-8 h-8 max-md:text-white" />
              )}
            </button>
          </div>

          {/* Logo */}
          <div className="flex-shrink-0 max-md:flex-1 max-md:flex max-md:justify-center max-md:items-center">
            <Link href="/">
              <Image
                alt="Qader Logo"
                src={isDark ? "/images/logodrk.png" : "/images/logo.svg"}
                width={100}
                height={40}
                className="max-md:hidden"
              />
             
              <Image
                alt="Qader Logo"
                src="/images/logo.png"
                width={100}
                height={40}
                className="max-md:flex hidden "
              />
            </Link>
          </div>

          {/* Desktop Menu */}
          <ul className="hidden lg:flex justify-center items-center gap-5">
            {navLinks.map((item) => (
              <li key={item.name}>
                <Link
                  href={item.ref}
                  className={` max-[1190px]:text-[13px] transition-colors hover:text-[#074182] text-[#074182] dark:text-[#3D93F5] dark:hover:text-[#3D93F5] ${
                    pathname === item.ref
                      ? " font-[600] "
                      : "text-black dark:text-[#FDFDFD]"
                  }`}
                >
                  {item.name}
                </Link>
              </li>
            ))}
            <ThemeToggle />
          </ul>

          {/* Desktop Buttons */}
          <div className="hidden md:flex items-center gap-3">
          
            <Button variant="outline" className=" border-[2px] hover:border-[2px] font-[700] hover:border-[#074182] dark:hover:border-[#3D93F5] dark:border-[#3D93F5] dark:bg-[#3D93F5] hover:dark:bg-white " onClick={openSignup}>
              <UserPlusIcon className="w-5 h-5 ml-1" />
              <span className="hidden lg:inline "> اشتراك</span>
            </Button>
            <Button variant="default" className="  border-[2px] font-[700] hover:border-[#074182] dark:hover:border-[#3D93F5] dark:border-[#3D93F5]" onClick={openLogin}>
              <UserIcon className="w-5 h-5 ml-1" />
              <span className="hidden lg:inline">تسجيل الدخول</span>
            </Button>
            
          </div>
        </nav>

        {/* Mobile Menu */}
        {showNav && (
          <div className="lg:hidden absolute top-full left-0 w-full bg-background dark:bg-slate-800 shadow-md z-40 transition-transform duration-300 ease-in-out">
            <ul className="flex flex-col items-start gap-1 px-5 py-4">
              {navLinks.map((item) => {
                const Icon = item.icon;
                return (
                  <li
                    key={item.name}
                    className="w-full border-b border-border last-of-type:border-b-0 py-3"
                  >
                    <Link
                      href={item.ref}
                      onClick={closeNav}
                      className={`font-bold transition-colors flex items-center gap-3 w-full ${
                        pathname === item.ref
                          ? "text-primary"
                          : "text-foreground hover:text-primary"
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      {item.name}
                    </Link>
                  </li>
                );
              })}
            </ul>

            {/* Mobile Buttons */}
            <div className="flex flex-col items-start gap-4 p-5 border-t border-border max-lg:hidden max-md:flex">
              <Button
                variant="outline"
                className="w-full  gap-2"
                onClick={() => {
                  openSignup();
                  closeNav();
                }}
              >
                <UserPlusIcon className="w-5 h-5" />
                <span> اشتراك</span>
              </Button>
              <Button
                variant="default"
                className="w-full gap-2"
                onClick={() => {
                  openLogin();
                  closeNav();
                }}
              >
                <UserIcon className="w-5 h-5" />
                <span>تسجيل الدخول</span>
              </Button>
              <div className="w-full flex justify-center pt-2">
                <ThemeToggle />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <LoginModal
        show={showLogin}
        onClose={() => setShowLogin(false)}
        onSwitchToSignup={switchToSignup} // Pass switch handler
      />
      <SignupModal
        show={showSignup}
        onClose={() => setShowSignup(false)}
        onSwitchToLogin={switchToLogin} // Pass switch handler
      />
    </>
  );
};

export default Navbar;
