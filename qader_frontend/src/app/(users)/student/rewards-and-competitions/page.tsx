"use client";

import React from "react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { StarIcon } from "@heroicons/react/24/outline";

const RewardsDashboard = () => {
  const testPoints = [
    { day: "الأحد", percent: 50 },
    { day: "الإثنين", percent: 30 },
    { day: "الثلاثاء", percent: 60 },
    { day: "الأربعاء", percent: 50 },
    { day: "الخميس", percent: 40 },
    { day: "الجمعة", percent: 60 },
    { day: "السبت", percent: 50 },
  ];

  const activeDays = [true, true, false, false, false, false, false];

  const storeItems = [
    {
      title: "تصاميم",
      desc: "استبدل 20 نقطة مقابل الحصول على تصاميم، شرح وافٍ لما ستحصل عليه.",
      points: 20,
    },
    {
      title: "الدخول للمسابقة الكبرى",
      desc: "استبدل 30 نقطة مقابل الدخول للمسابقة الكبرى، التي سيتم الإعلان عنها لاحقاً.",
      points: 30,
    },
    {
      title: "أشعار",
      desc: "استبدل 10 نقاط مقابل الحصول على أشعار، شرح وافٍ لما ستحصل عليه.",
      points: 10,
    },
    {
      title: "مخطوطة",
      desc: "استبدل 5 نقاط مقابل الحصول على مخطوطة، شرح وافٍ لما ستحصل عليه.",
      points: 5,
    },
  ];

  return (
    <div className="p-5 space-y-6">
      <div className="flex flex-wrap gap-6">
        {/* Test Points Section */}
        <div className="flex-1 min-w-[300px] border rounded-2xl p-5">
          <p className="font-bold mb-2">النقاط الاختبارات</p>
          <div className="text-3xl font-bold text-center mb-1">50</div>
          <p className="text-sm text-center text-gray-500 mb-4">نقطة</p>
          <div className="flex justify-around items-end h-40">
            {testPoints.map((item, index) => (
              <div key={index} className="text-center">
                <div className="w-3 h-32 bg-gray-200 rounded-2xl overflow-hidden relative">
                  <div
                    className="absolute bottom-0 w-full bg-[#2f80ed] rounded-b-2xl"
                    style={{ height: `${item.percent}%` }}
                  />
                </div>
                <div className="text-xs mt-2">{item.day}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Achievement and Weekly Stars Section */}
        <div className="flex-1 min-w-[300px] border rounded-2xl p-5 space-y-4">
          <div>
            <p className="font-bold mb-1">شارات الإنجاز</p>
            <p className="text-2xl font-bold">12</p>
            <p className="text-sm text-gray-500">شارة إنجاز</p>
            <div className="mt-2 flex flex-wrap gap-1 text-xl">
              <span>🏅</span>
              <span>🏆</span>
              <span>🔥</span>
              <span>🌟</span>
              <span>💯</span>
              <span>🎯</span>
              <span>🚀</span>
            </div>
          </div>
          <div>
            <p className="font-bold mb-1">نقاط الأيام التالية</p>
            <p className="text-2xl font-bold">30</p>
            <p className="text-sm text-gray-500 mb-1">نقطة</p>
            <div className="flex items-center">
              <StarIcon className="w-8 h-8 text-[#2f80ed]" />
              <div className="ml-2">
                <p className="text-sm">يومان متتاليان</p>
                <div className="flex items-center gap-2">
                  <div className="flex w-16 h-2 overflow-hidden rounded-full">
                    <span className="w-[40%] bg-[#2f80ed]" />
                    <span className="w-[60%] bg-gray-300" />
                  </div>
                  <span className="text-xs">2/5</span>
                </div>
              </div>
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              {["الأحد", "الإثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"].map((day, idx) => (
                <div key={idx} className="flex items-center text-xs">
                  <StarIcon className={`w-4 h-4 mr-1 ${activeDays[idx] ? "text-[#2f80ed]" : "text-gray-400"}`} />
                  {day}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Store Section */}
      <div className="border p-5 rounded-2xl">
        <p className="font-bold mb-5">متجر المكافآت</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {storeItems.map((item, index) => (
            <div key={index} className="border rounded-xl p-4 flex flex-col justify-between">
              <div>
                <p className="font-bold mb-1">{item.title}</p>
                <p className="text-sm text-gray-600">{item.desc}</p>
              </div>
              <div className="flex items-center justify-between mt-4">
                <Image src="/images/gift.png" alt="كأس" width={50} height={50} />
                <Button className="bg-[#074182] text-white px-4 py-2 rounded-lg hover:bg-[#053866]">
                  استبدال
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RewardsDashboard;
