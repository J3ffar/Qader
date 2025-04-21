"use client";
import React, { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button"; // Assuming ui is directly under components
import { ThemeToggle } from "@/components/ui/theme-toggle"; // Assuming ui is directly under components
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

// Define nav data outside the component
const navLinks = [
  { name: "الرئيسية", ref: "/", icon: HomeIcon },
  { name: "قصتنا", ref: "/about", icon: BookOpenIcon },
  { name: "شركاء النجاح", ref: "/partners", icon: UsersIcon },
  { name: "صفحة المذكرة", ref: "/notes", icon: PencilIcon },
  { name: "الأسئلة الشائعة", ref: "/faq", icon: QuestionMarkCircleIcon },
  { name: "تواصل معنا", ref: "/contact", icon: ChatBubbleOvalLeftEllipsisIcon },
];

const Navbar = () => {
  const [showNav, setShowNav] = useState(false);
  const [showPopup, setShowPopup] = useState(false);
  const pathname = usePathname();

  const handleNav = () => setShowNav(!showNav);
  const togglePopup = () => setShowPopup(!showPopup);
  const closeNav = () => setShowNav(false); // Helper to close nav on link click

  return (
    <>
      <nav className="flex justify-between items-center shadow-lg px-4 sm:px-8 md:px-16 py-4 relative w-full bg-background max-md:bg-[#074182] max-md:flex-row-reverse max-md:gap-6">
        {" "}
        {/* Use bg-background for theme, adjusted padding */}
        {/* Hamburger Icon */}
        <div className="lg:hidden">
          {" "}
          {/* Changed breakpoint logic slightly */}
          <button
            onClick={handleNav}
            aria-label={showNav ? "Close menu" : "Open menu"}
          >
            {" "}
            {/* Use button for accessibility */}
            {showNav ? (
              <XMarkIcon className="w-8 h-8 text-[#074182] dark:text-white cursor-pointer max-md:text-white" />
            ) : (
              <Bars3Icon className="w-8 h-8 text-[#074182] dark:text-white cursor-pointer max-md:text-white" />
            )}
          </button>
        </div>
        {/* Logo */}
        <div className="flex-shrink-0 max-md:flex-1 max-md:flex max-md:justify-center max-md:items-center">
          {" "}
          {/* Ensure logo doesn't shrink */}
          <Link href="/">
            <Image
              alt="Qader Logo"
              src="/images/logo.svg" // Prefer SVG for logos
              width={100}
              height={40} // Adjust height based on actual logo aspect ratio
              priority
            />
          </Link>
        </div>
        {/* Desktop Menu */}
        <ul className="hidden lg:flex justify-center items-center gap-5">
          {navLinks.map((item) => (
            <li key={item.name}>
              <Link
                href={item.ref}
                className={`font-bold transition-colors duration-300 hover:text-primary ${
                  // Use primary color from theme
                  pathname === item.ref
                    ? "text-primary" // Use primary color for active
                    : "text-muted-foreground" // Use muted color for inactive
                }`}
              >
                {item.name}
              </Link>
            </li>
          ))}
        </ul>
        {/* Buttons - Desktop only */}
        <div className="hidden md:flex items-center gap-3">
          <Button variant="outline" onClick={togglePopup}>
            <UserPlusIcon className="w-5 h-5 ml-1" /> {/* Adjusted margin */}
            <span className="hidden xl:inline"> اشتراك</span>{" "}
            {/* Use hidden xl:inline */}
          </Button>
          <Button variant="default" onClick={togglePopup}>
            <UserIcon className="w-5 h-5 ml-1" /> {/* Adjusted margin */}
            <span className="hidden xl:inline">تسجيل الدخول</span>{" "}
            {/* Use hidden xl:inline */}
          </Button>
          <ThemeToggle />
        </div>
      </nav>

      {/* Mobile Menu Overlay */}
      {showNav && (
        <div
          className={`lg:hidden absolute top-full left-0 w-full bg-background dark:bg-slate-800 shadow-md z-50 transition-transform duration-300 ease-in-out ${
            showNav ? "transform translate-y-0" : "transform -translate-y-full"
          }`} // Added transition
        >
          <ul className="flex flex-col items-start gap-1 px-5 py-4">
            {" "}
            {/* Use ul */}
            {navLinks.map((item) => {
              const Icon = item.icon;
              return (
                <li
                  key={item.name}
                  className="w-full border-b border-border last-of-type:border-b-0 py-3 list-none"
                >
                  {" "}
                  {/* Use li, border color from theme */}
                  <Link
                    href={item.ref}
                    onClick={closeNav} // Close nav on click
                    className={`font-bold transition-colors duration-300 flex items-center gap-3 w-full ${
                      // Added w-full
                      pathname === item.ref
                        ? "text-primary" // Use primary color for active
                        : "text-foreground hover:text-primary" // Use theme colors
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
          {/* Buttons inside Mobile Menu */}
          <div className="flex flex-col items-start gap-4 p-5 border-t border-border">
            {" "}
            {/* Use theme border color */}
            <Button
              variant="outline"
              className="w-full justify-start gap-2"
              onClick={() => {
                togglePopup();
                closeNav();
              }}
            >
              {" "}
              {/* Added justify-start */}
              <UserPlusIcon className="w-5 h-5" />
              <span> اشتراك</span>
            </Button>
            <Button
              variant="default"
              className="w-full justify-start gap-2"
              onClick={() => {
                togglePopup();
                closeNav();
              }}
            >
              {" "}
              {/* Added justify-start */}
              <UserIcon className="w-5 h-5" />
              <span>تسجيل الدخول</span>
            </Button>
            <div className="w-full flex justify-start pt-2">
              {" "}
              {/* Align theme toggle */}
              <ThemeToggle />
            </div>
          </div>
        </div>
      )}

      {/* Auth Popup */}
      {showPopup && (
        <>
          {/* Overlay */}
          <div
            className="fixed inset-0 bg-black/30 dark:bg-black/50 z-40" // Adjusted opacity
            onClick={togglePopup}
            aria-hidden="true"
          />

          {/* Popup Content */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="relative bg-background p-8 sm:p-10 rounded-2xl w-full max-w-md shadow-xl transition-all duration-300 ease-out scale-95 opacity-0 animate-fade-in-scale">
              {" "}
              {/* Use bg-background, added animation */}
              {/* Close Button */}
              <button
                onClick={togglePopup}
                className="absolute top-3 right-3 text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Close popup"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
              {/* Popup Body */}
              <div className="space-y-6 mt-4">
                {" "}
                {/* Reduced spacing slightly */}
                {/* New Account Section */}
                <div className="flex flex-col justify-center items-center text-center">
                  <p className="text-foreground font-bold text-xl sm:text-2xl">
                    ليس لديك حساب في موقعنا؟
                  </p>
                  {/* Use actual Link or router push */}
                  <Button
                    variant="outline"
                    className="mt-4 w-full max-w-xs"
                    onClick={togglePopup}
                  >
                    <Link href="/signup">انشاء حساب جديد</Link>{" "}
                    {/* Example link */}
                  </Button>
                </div>
                <hr className="border-border" /> {/* Use theme border */}
                {/* Login Section */}
                <div className="flex flex-col justify-center items-center text-center">
                  <p className="text-foreground font-bold text-xl sm:text-2xl">
                    لديك حساب سابق؟
                  </p>
                  {/* Use actual Link or router push */}
                  <Button
                    variant="default"
                    className="mt-4 w-full max-w-xs"
                    onClick={togglePopup}
                  >
                    {" "}
                    {/* Use default variant */}
                    <Link href="/login">تسجيل دخول</Link> {/* Example link */}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
};

export default Navbar;
