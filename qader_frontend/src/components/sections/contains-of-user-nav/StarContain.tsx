"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { StarIcon, EyeIcon } from "@heroicons/react/24/outline";

const StarContain = ({ showStarContainer }: { showStarContainer: boolean }) => {
  if (!showStarContainer) {
    return null;
  }

  const days = [
    { name: "الاحد", active: true },
    { name: "الاثنين", active: true },
    { name: "الثلاثاء", active: false },
    { name: "الاربعاء", active: false },
    { name: "الخميس", active: false },
    { name: "الجمعة", active: false },
    { name: "السبت", active: false },
  ];

  return (
    <div className="absolute top-20 left-40 starcontain p-5 rounded-2xl text-base border-2 flex flex-col bg-white shadow-lg w-72 transition-all duration-300">
      <p className="font-bold">استمر لتحسين نقاط الايام</p>
      <p className="text-gray-500 mt-1">هذه هى جميع نقاط الاسبوع التى من الالتزام</p>

      <div className="flex items-center mt-4">
        <StarIcon className="w-10 h-10 mr-2 text-[#2f80ed]" />
        <div>
          <p>يومان متتاليان</p>
          <div className="flex items-center gap-2 mt-1">
            <div className="flex w-14 h-2 overflow-hidden rounded-2xl">
              <span className="w-[70%] h-full bg-gray-400"></span>
              <span className="w-[30%] h-full bg-[#074182]"></span>
            </div>
            <span className="text-xs">2/5</span>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 mt-5 justify-center">
        {days.map((day, index) => (
          <div key={index} className="flex items-center text-xs">
            <StarIcon className={`w-5 h-5 mr-1 ${day.active ? "text-[#2f80ed]" : "text-gray-400"}`} />
            {day.name}
          </div>
        ))}
      </div>

      <div className="flex justify-center mt-5">
        <Button variant="outline" className="flex items-center gap-2">
          <EyeIcon className="w-5 h-5" />
          عرض الكل
        </Button>
      </div>
    </div>
  );
};

export default StarContain;
