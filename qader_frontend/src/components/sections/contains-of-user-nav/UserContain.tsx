"use client";

import React from 'react';
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
  Cog6ToothIcon,
  ExclamationCircleIcon,
  Squares2X2Icon,
  QuestionMarkCircleIcon,
  ArrowLeftStartOnRectangleIcon
} from "@heroicons/react/24/outline";

interface UserContainProps {
  showUserContain: boolean;
}

const UserContain = ({ showUserContain }: UserContainProps) => {
  if (!showUserContain) return null; // حماية إضافية ضد الـ Hydration mismatch

  return (
    <div className="Usercontain absolute left-2 top-16 bg-white border rounded-2xl mt-2 w-96 flex flex-col items-center">
      <div className="flex flex-col items-center py-4">
        <div className="w-12 h-12 bg-gray-200 rounded-full relative">
          <span className="w-3 h-3 rounded-full bg-[#27ae60] absolute top-1 right-0 border-2 border-white"></span>
        </div>
        <p className="text-lg font-medium">سالم سعيد</p>
      </div>

      <div className="flex items-center gap-2 border-b w-full py-3 px-4">
        <Cog6ToothIcon className="w-5 h-5" />
        <p>الإعدادات</p>
      </div>

      <div className="flex items-center gap-2 w-full py-3 px-4">
        <ExclamationCircleIcon className="w-5 h-5" />
        <p>وضع الطوارئ</p>
      </div>

      <div className="flex items-center justify-between gap-2 border-b w-full py-3 px-4">
        <p className="flex gap-2">
          <Squares2X2Icon className="w-5 h-5" /> السمات
        </p>
        <ThemeToggle />
      </div>

      <div className="flex items-center gap-2 w-full py-3 px-4">
        <QuestionMarkCircleIcon className="w-5 h-5" />
        <p>الدعم الإدارى</p>
      </div>

      <div className="flex items-center gap-2 w-full py-3 px-4">
        <ArrowLeftStartOnRectangleIcon className="w-5 h-5" />
        <p>تسجيل خروج</p>
      </div>
    </div>
  );
};

export default UserContain;
