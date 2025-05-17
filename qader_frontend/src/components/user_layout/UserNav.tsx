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
      className=" flex flex-col bg-white dark:bg-[#081028] border-[0.5px] border-[#7E89AC] shadow-sm h-auto pr-5 pl-5 transition-all duration-300 z-40 max-md:py-3"
      style={{
        right: isOpen ? 110 : 50,
        left: 0,
      }}
    >
      {/* Input + Search Button */}
      <div className="flex flex-col-reverse lg:flex-row items-center justify-between lg:h-[70px] p-4 gap-6 lg:gap-0">
  {/* Search Bar */}
  <div className="flex flex-1 justify-center items-center w-full lg:w-auto">
    <div className="flex w-full max-w-md items-center bg-white dark:bg-transparent border rounded-lg overflow-hidden">
    <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 mr-3" />
      <input
        type="text"
        placeholder="اكتب سؤالك هنا"
        className="flex-1 p-2 pr-10 text-right focus:outline-none "
      />

    </div>
    <button className="bg-[#074182] text-white p-2 rounded-lg ml-2 hover:bg-[#053866] transition mr-2">
      <MagnifyingGlassIcon className="w-6 h-6" />
    </button>
  </div>

  {/* Icons */}
  <div className="flex items-center gap-4">
    <span
      className={`flex items-center gap-1 cursor-pointer rounded-xl p-2 ${
        showStarContainer ? "bg-gray-100 dark:bg-transparent" : "hover:bg-gray-100 dark:hover:bg-gray-100/20"
      }`}
      onClick={toggleStarContainer}
    >
      <StarIcon className="w-6 h-6" /> 11
    </span>

    <span
      className={`flex items-center gap-1 cursor-pointer rounded-xl p-2 ${
        showShapContain ? "bg-gray-100 dark:bg-transparent" : "hover:bg-gray-100 dark:hover:bg-gray-100/20"
      }`}
      onClick={toggleShapContain}
    >
      <Image src="/images/hexagon.png" width={25} height={25} alt="hexagon" /> 12
    </span>

    <span
      className={`relative cursor-pointer rounded-xl p-2 ${
        isVisible ? "bg-gray-100 dark:bg-transparent" : "hover:bg-gray-100 dark:hover:bg-gray-100/20"
      }`}
      onClick={toggleVisibility}
    >
      <GiftIcon className="w-6 h-6" />
      <span className="absolute w-3 h-3 bg-red-500 rounded-full bottom-6 border-2 border-white"></span>
    </span>
  </div>

  {/* Notifications and User */}
  <div className="flex items-center gap-4">
    <span
      className={`relative cursor-pointer rounded-xl p-2 ${
        showBellDropdown ? "bg-gray-100 dark:bg-transparent" : "hover:bg-gray-100 dark:hover:bg-gray-100/20"
      }`}
      onClick={toggleBellDropdown}
    >
      <BellIcon className="w-6 h-6" />
      <span className="absolute w-3 h-3 bg-red-500 rounded-full bottom-6 border-2 border-white"></span>
    </span>

    <div
      onClick={toggleUserContain}
      className={`relative flex items-center gap-2 cursor-pointer rounded-xl p-2  ${
        showUserContain ? "bg-gray-100 dark:bg-transparent" : "hover:bg-gray-100 dark:hover:bg-gray-100/20 "
      }`}
    >
      <div className="w-10 h-10 bg-gray-200  rounded-full relative">
        <span className="absolute top-1 right-0 w-3 h-3 bg-[#27ae60] rounded-full border-2 border-white"></span>
      </div>
      <div className="hidden max-md:hidden md:flex flex-col items-end">
        <p className="text-sm font-medium">سالم سعيد</p>
        <p className="text-xs text-gray-400">صباح الخير</p>
      </div>
      <ChevronDownIcon className="w-6 h-6 text-gray-600" />
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
