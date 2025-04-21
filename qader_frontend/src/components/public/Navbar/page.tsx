"use client"
import React, { useState } from 'react';
import Link from 'next/link';
import { Button } from "@/components/ui/button"
import { Bars3Icon, XMarkIcon, UserIcon, UserPlusIcon, HomeIcon, BookOpenIcon, PencilIcon, UsersIcon, QuestionMarkCircleIcon, ChatBubbleOvalLeftEllipsisIcon } from '@heroicons/react/24/solid';
import { ThemeToggle } from '@/components/theme-toggle';
import Image from 'next/image'
import { usePathname } from 'next/navigation';

const Navbar = () => {
  const [showNav, setShowNav] = useState(false);
  const pathname = usePathname(); // 

  const nav = [
  { name: 'الرئيسية', ref: '/', icon: HomeIcon },
  { name: 'قصتنا', ref: '/about', icon: BookOpenIcon },
  { name: 'شركاء النجاح', ref: '/partners', icon: UsersIcon },
  { name: 'صفحة المذكرة', ref: '/notes', icon: PencilIcon },
  { name: 'الأسئلة الشائعة', ref: '/faq', icon: QuestionMarkCircleIcon },
  { name: 'تواصل معنا', ref: '/contact', icon: ChatBubbleOvalLeftEllipsisIcon }
];

  const handleNav = () => {
    setShowNav(!showNav)
  }

  const [showPopup, setShowPopup] = useState(false);
  const togglePopup = () => setShowPopup(!showPopup);

  return (
    <nav className='flex justify-between items-center shadow-lg px-16 py-7 relative  w-screen max-md:bg-[#074182] max-md:flex-row-reverse max-md:gap-6'>
      {/* Hamburger Icon */}
      <div className="hidden max-lg:flex max-md:flex-none">
        {showNav ? (
          <XMarkIcon className="w-9 h-9 text-[#074182] cursor-pointer max-md:text-white" onClick={handleNav} />
        ) : (
          <Bars3Icon className="w-9 h-9 text-[#074182] cursor-pointer max-md:text-white" onClick={handleNav} />
        )}
      </div>

      <div className='max-md:flex-1/2 max-md:flex max-md:justify-center max-md:items-center max-md:rounded-xl max-md:bg-[#e7f1fe]'><Image alt='' src={"/images/logo.svg"} width={100} height={100}/></div>

      {/* Desktop Menu */}
      <ul className='flex justify-center items-center gap-5 max-lg:hidden'>
        {nav.map((item, index) => (
          <li key={index}>
            <Link
              href={item.ref}
              className={`font-bold transition-colors duration-300 hover:text-[#032c58] ${
                pathname === item.ref ? "text-[#032c58]" : "text-gray-500"
              }`}
            >
              {item.name}
            </Link>
          </li>
        ))}
      </ul>

  
      {/* Mobile Menu */}
{showNav && (
  <div className="flex flex-col items-start gap-3 absolute top-full left-0 w-full bg-white px-5 py-4 max-lg:flex shadow-md z-50">
    {/* Links */}
    {nav.map((item, index) => {
      const Icon = item.icon;
      return (
        <li key={index} className="w-full border-b last-of-type:border-b-0 py-2 list-none">
          <Link
            href={item.ref}
            className={`font-bold transition-colors duration-300 flex items-center gap-2 ${
              pathname === item.ref ? "text-[#032c58]" : "text-gray-500"
            }`}
          >
            <Icon className="w-5 h-5" />
            {item.name}
          </Link>
        </li>
      );
    })}

    {/* Buttons under menu */}
    <div className="hidden  items-start w-full mt-4 max-md:flex max-md:flex-col gap-4">
      <Button variant="outline"  onClick={togglePopup}>
              <UserPlusIcon className="w-5 h-5" />
              <span > اشتراك</span>
      </Button>
      <Button variant="default" onClick={togglePopup}>
              <UserIcon className="w-5 h-5" />
              <span>تسجيل الدخول</span>
      </Button>
      <ThemeToggle />
    </div>
  </div>
)}

      {/* Buttons */}
      {/* Buttons - Desktop only */}
<div className='gap-3 max-md:hidden flex items-center'>
  <Button variant="outline" onClick={togglePopup}>
    <UserPlusIcon className="w-5 h-5" />
    <span className='max-xl:hidden'> اشتراك</span>
  </Button>
  <Button variant="default" onClick={togglePopup}>
    <UserIcon className="w-5 h-5" />
    <span className='max-xl:hidden'>تسجيل الدخول</span>
  </Button>
  <ThemeToggle />
</div>



      {/* Popup */}
      {showPopup && (
        <>
          <div
            className="fixed inset-0 bg-black/15 bg-opacity-50 z-40"
            onClick={togglePopup}
          />

          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="relative bg-white p-14 rounded-2xl w-[90%] max-w-md shadow-lg transition-all duration-500">
              <button
                onClick={togglePopup} className="absolute top-3 right-3 text-[#4f008d] transition">
                <XMarkIcon className="w-6 h-6" />
              </button>

              <div className="space-y-7 mt-7">
                <div className='flex flex-col justify-center items-center'>
                  <p className="text-gray-700 font-bold text-center text-2xl">ليس لديك حساب في موقعنا؟</p>
                  <Button variant="outline" className="mt-4">
                    <Link href="/">انشاء حساب جديد</Link>
                  </Button>
                </div>
                
                <hr className="border-gray-500" />

                <div className='flex flex-col justify-center items-center text-2xl'>
                  <p className="text-gray-700 font-bold">لديك حساب سابق؟</p>
                  <Button variant="outline" className="mt-4">
                    <Link href="/">تسجيل دخول</Link>
                  </Button>
                </div>
              </div>

            </div>
          </div>
        </>
      )}

      
    </nav>
  );
};

export default Navbar;
