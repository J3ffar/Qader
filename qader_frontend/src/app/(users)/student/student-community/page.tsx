"use client";

import React, { useState } from "react";
import Image from "next/image";
import { PaperAirplaneIcon, ChatBubbleOvalLeftIcon, HeartIcon, FunnelIcon } from "@heroicons/react/24/outline";
import PublishDiscussionModal from "./popup";

const categories = [
  "النقاشات الدراسية",
  "الاختبارات",
  "طلب زمالة",
  "النصائح والتجارب",
  "مسابقات شهرية",
];

const StudentCommunity: React.FC = () => {
     const [showModal, setShowModal] = useState(false);
  return (
    <div className="bg-white p-6 rounded-lg  mx-auto">
      {/* Header */}
      <div className="text-right mb-6">
        <h1 className="text-2xl font-bold text-gray-900">مجتمع الطلاب</h1>
        <p className="text-gray-500 mt-1">
          المجتمع الذي يجمعك مع زملائك لتشاركوا التجارب.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 justify-end mb-6">
        {categories.map((cat, idx) => (
          <button
            key={idx}
            className={`px-4 py-2 border rounded-full text-sm font-medium ${
              cat === "النقاشات الدراسية"
                ? "bg-[#074182] text-white"
                : "border-gray-300 text-gray-700 hover:bg-gray-100"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Filter & Post Button */}
      <div className="flex justify-between items-center mb-4">
        <button
        onClick={() => setShowModal(true)}
        className="bg-[#074182] text-white px-4 py-2 rounded-md"
      >
        نشر مناقشة
      </button>
        <FunnelIcon className="w-5 h-5 text-gray-600 cursor-pointer" />
      </div>

      {/* Discussion Card */}
      <div className="border border-gray-200 rounded-lg p-4 mb-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-2">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
            <div className="text-right">
              <p className="text-sm font-bold text-gray-800">بيار سعيد</p>
              <p className="text-xs text-gray-500">ثالث ثانوي</p>
            </div>
          </div>
          <p className="text-sm text-gray-400">منذ 2 ساعة</p>
        </div>

        {/* Text */}
        <p className="text-right text-sm text-gray-700 leading-relaxed mb-3 line-clamp-3">
          نص المناقشة نص المناقشة نص المناقشة نص المناقشة نص المناقشة نص المناقشة نص المناقشة نص المناقشة...
          <button className="text-blue-600 text-sm ml-1">عرض المزيد</button>
        </p>

        {/* Image */}
        <div className="rounded-lg overflow-hidden mb-4">
          <Image
            src="/images/discussion.jpg" // Replace with real image
            alt="discussion"
            width={800}
            height={400}
            className="w-full h-auto object-cover"
          />
        </div>

        {/* Reactions */}
        <div className="flex justify-between text-sm text-gray-500 border-t pt-2">
          <p>10 إعجاب</p>
          <p>8 تعليقات</p>
        </div>

        {/* Buttons */}
        <div className="flex justify-between mt-3 border-t pt-2">
          <button className="flex items-center gap-1 text-gray-600 hover:text-blue-600">
            <HeartIcon className="w-5 h-5" />
            إعجاب
          </button>
          <button className="flex items-center gap-1 text-gray-600 hover:text-blue-600">
            <ChatBubbleOvalLeftIcon className="w-5 h-5" />
            تعليقات
          </button>
        </div>

        {/* Comment Box */}
        <div className="flex items-center gap-2 mt-4 border-t pt-3">
          <input
            type="text"
            placeholder="اكتب تعليقا..."
            className="flex-1 border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button className="bg-[#074182] text-white px-4 py-2 rounded-md text-sm font-medium flex items-center gap-1">
            إرسال
            <PaperAirplaneIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      <PublishDiscussionModal show={showModal} onClose={() => setShowModal(false)} />
    </div>
  );
};

export default StudentCommunity;
