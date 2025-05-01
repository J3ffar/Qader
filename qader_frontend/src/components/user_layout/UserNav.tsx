"use client";

import { useState } from "react";
import Image from "next/image";
import {
  MagnifyingGlassIcon,
  StarIcon,
  GiftIcon,
  BellIcon,
  ChevronDownIcon,
} from "@heroicons/react/24/outline";
import Shapcontain from "@/components/sections/contains-of-user-nav/ShapContain";
import StarContain from "@/components/sections/contains-of-user-nav/StarContain";
import GiftContain from "@/components/sections/contains-of-user-nav/GiftContain";
import BellShap from "@/components/sections/contains-of-user-nav/BellContain";
import UserContain from "@/components/sections/contains-of-user-nav/UserContain";

interface UserNavbarProps {
  isOpen: boolean;
}

const UserNavbar = ({ isOpen }: UserNavbarProps) => {
  const [showStarContainer, setShowStarContainer] = useState(false);
  const [showShapContain, setShowShapContain] = useState(false);
  const [activeSection, setActiveSection] = useState<"invite" | "store">("invite");
  const [isVisible, setIsVisible] = useState(false);
  const [showBellDropdown, setShowBellDropdown] = useState(false);
  const [showUserContain, setShowUserContain] = useState(false);

  const toggleStarContainer = () => {
    setShowStarContainer((prev) => !prev);
  };

  const toggleShapContain = () => {
    setShowShapContain((prev) => !prev);
  };

  const toggleVisibility = () => {
    setIsVisible((prev) => !prev);
  };

  const toggleBellDropdown = () => {
    setShowBellDropdown((prev) => !prev);
  };

  const toggleUserContain = () => {
    setShowUserContain((prev) => !prev);
  };

  return (
    <div
      className="fixed top-0 flex flex-col bg-white shadow-sm h-auto pr-5 pl-5 transition-all duration-300 z-40 max-md:py-3"
      style={{
        right: isOpen ? 110 : 50,
        left: 0,
      }}
    >
      {/* Input + Search Button */}
      <div className="flex items-center h-[70px]  max-md:gap-7 max-md:h-full">
        <div className="flex items-center flex-1 mr-32">
          <div className="relative w-fit mr-4 max-md:hidden">
            <input
              type="text"
              placeholder="اكتب سؤالك هنا"
              className="border hover:border-gray-300 rounded-lg py-2 pr-10 focus:outline-none focus:ring-[#074182] max-md:max-w-3xs"
            />
            <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute right-3 top-1/2 transform -translate-y-1/2" />
          </div>
          <button className="bg-[#074182] text-white p-2 rounded-lg hover:bg-[#053866] transition ml-2 max-md:hidden">
            <MagnifyingGlassIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Icons */}
        <div className="flex items-center gap-4 pl-2 border-l-1 relative max-md:left-36">
          <span
            className={`flex items-center gap-1 cursor-pointer rounded-xl p-2 ${
              showStarContainer ? "bg-gray-100" : "hover:bg-gray-100"
            }`}
            onClick={toggleStarContainer}
          >
            <StarIcon className="w-6 h-6" /> 11
          </span>

          <span
            className={`flex items-center justify-center gap-1 cursor-pointer rounded-xl px-4 py-2 ${
              showShapContain ? "bg-gray-100" : "hover:bg-gray-100"
            }`}
            onClick={toggleShapContain}
          >
            <Image src="/images/hexagon.png" width={25} height={25} alt="hexagon" /> 12
          </span>

          <span
            className={`relative cursor-pointer rounded-xl p-2 ${
              isVisible ? "bg-gray-100" : "hover:bg-gray-100"
            }`}
            onClick={toggleVisibility}
          >
            <GiftIcon className="w-6 h-6" />
            <span className="w-3 h-3 rounded-full bg-red-500 absolute bottom-6 border-2 border-white"></span>
          </span>
        </div>

        {/* Notifications and User */}
        <div className="flex items-center gap-3 ml-5 pr-2 relative max-md:left-36">
          <span
            className={`Bell relative cursor-pointer rounded-xl p-2 ${
              showBellDropdown ? "bg-gray-100" : "hover:bg-gray-100"
            }`}
            onClick={toggleBellDropdown}
          >
            <BellIcon className="w-6 h-6" />
            <span className="w-3 h-3 rounded-full bg-red-500 absolute bottom-6 border-2 border-white"></span>
          </span>

          <div
            onClick={toggleUserContain}
            className={`relative flex items-center gap-2 cursor-pointer rounded-xl p-2 ${
              showUserContain ? "bg-gray-100" : "hover:bg-gray-100"
            }`}
          >
            <div className="w-10 h-10 bg-gray-200 rounded-full relative">
              <span className="w-3 h-3 rounded-full bg-[#27ae60] absolute top-1 right-0 border-2 border-white"></span>
            </div>
            <div className="max-md:hidden">
              <p className="text-sm font-medium">سالم سعيد</p>
              <p className="text-xs text-gray-400">صباح الخير</p>
            </div>
            <ChevronDownIcon className="w-7 h-7 text-gray-600 mr-11 max-md:mr-5" />
          </div>
        </div>
      </div>

      {/* Other Containers */}
      <Shapcontain showShapContain={showShapContain} />
      <GiftContain
        isVisible={isVisible}
        activeSection={activeSection}
        setActiveSection={setActiveSection}
      />
      <StarContain showStarContainer={showStarContainer} />
      <BellShap showBellDropdown={showBellDropdown} />
      <UserContain showUserContain={showUserContain} />
    </div>
  );
};

export default UserNavbar;
