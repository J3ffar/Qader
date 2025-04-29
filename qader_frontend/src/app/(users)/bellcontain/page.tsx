"use client";

import React from "react";
import Image from "next/image";

const BellShap = ({ showBellDropdown }: { showBellDropdown: boolean }) => {
  if (!showBellDropdown) return null; // الحل الصح لتفادي مشكلة Hydration

  return (
    <div className="bellshap absolute top-[70px] left-0 w-80 bg-white shadow-lg rounded-2xl border p-4 z-50">
      <div className="flex justify-between items-center gap-20 py-3">
        <p className="font-bold">الإشعارات</p>
        <span className="text-[#074182] text-sm cursor-pointer">وضع علامة مقروء للجميع</span>
      </div>

      {[...Array(4)].map((_, index) => (
        <div key={index} className="border-t py-3">
          <div className="flex items-center gap-2">
            <Image src="/images/course logo.png" width={30} height={30} alt="notification" />
            <p className="font-bold text-sm">وصف للاشعار</p>
          </div>
          <span className="text-gray-500 text-xs">. منذ يومان</span>
        </div>
      ))}
    </div>
  );
};

export default BellShap;
