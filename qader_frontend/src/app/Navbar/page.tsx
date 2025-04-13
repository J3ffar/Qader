"use client"
import React, { useState } from 'react';
import Link from 'next/link';
import { Button } from "@/components/ui/button"
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/solid';

const Navbar = () => {
  const [showNav, setShowNav] = useState(false);
  const nav = [
    { name: 'الرئيسية', ref: '/' },
    { name: 'المسارات', ref: '/' },
    { name: 'الاسئلة الشائعة', ref: '/' },
    { name: 'المدونة', ref: '/' },
    { name: 'الأسعار', ref: '/' }
  ];

  const handleNav = () => {
    setShowNav(!showNav)
  }
const [showPopup, setShowPopup] = useState(false);

  const togglePopup = () => setShowPopup(!showPopup);
  return (
    <nav className='flex justify-between items-center shadow-lg px-16 py-7 relative w-screen'>
      {/* Hamburger and Close Icon */}
      <div className="hidden max-md:flex">
        {showNav ? (
          <XMarkIcon className="w-9 h-9 text-[#4f008d] cursor-pointer" onClick={handleNav} />
        ) : (
          <Bars3Icon className="w-9 h-9 text-[#4f008d] cursor-pointer" onClick={handleNav} />
        )}
      </div>

      <div className='text-[#4f008d] font-bold text-4xl'>logo</div>

      {/* Desktop Menu */}
      <ul className='flex justify-center items-center gap-5 max-md:hidden'>
        {nav.map((item, index) => (
          <li key={index} className='text-gray-500 font-bold'>
            <Link href={item.ref}>{item.name}</Link>
          </li>
        ))}
      </ul>

      {/* Mobile Menu */}
      <ul
  className={`flex flex-col justify-center items-start gap-3 absolute top-full left-0 w-full bg-white px-5 py-4 max-md:flex md:hidden shadow-md
  transform transition-transform duration-500 ease-in-out
  ${showNav ? "translate-x-0" : "translate-x-full"}
  `}
>
  {nav.map((item, index) => (
    <li key={index} className='text-gray-500 font-bold w-full border-b last-of-type:border-b-0 py-2'>
      <Link href={item.ref}>{item.name}</Link>
    </li>
  ))}
</ul>
        <Button variant="outline" onClick={togglePopup}>login</Button>

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
