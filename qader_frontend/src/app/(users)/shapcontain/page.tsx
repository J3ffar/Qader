"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { EyeIcon } from "@heroicons/react/24/outline";

function Shapcontain({ showShapContain }: { showShapContain: boolean }) {
  if (!showShapContain) {
    return null;
  }

  const days = [
    { name: "الاحد", percent: 50 },
    { name: "الاثنين", percent: 30 },
    { name: "الثلاثاء", percent: 20 },
    { name: "الاربعاء", percent: 40 },
    { name: "الخميس", percent: 50 },
    { name: "الجمعة", percent: 60 },
    { name: "السبت", percent: 100 },
  ];

  return (
    <div className="Shapcontain absolute top-[80px] left-20 starcontain p-5 rounded-2xl text-base border-2 flex flex-col bg-white shadow-lg w-72 transition-all duration-300">
      <p className="font-bold">ابدأ التعلم لكسب المزيد من النقاط</p>
      <p className="text-gray-500 mt-1">هذه هى جميع نقاط الاسبوع التى جمعتها</p>

      <div className="flex gap-2 items-center justify-center text-xs mt-4">
        {days.map((day, index) => (
          <div key={index} className="relative text-center">
            <span className="w-3 h-40 rounded-2xl bg-gray-100 block relative overflow-hidden">
              <span
                className="absolute bottom-0 left-0 w-full bg-[#2f80ed] rounded-b-2xl"
                style={{ height: `${day.percent}%` }}
              ></span>
            </span>
            <div className="mt-1">{day.name}</div>
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
}

export default Shapcontain;
