"use client";

import React from "react";
import { PaperAirplaneIcon, MicrophoneIcon, PencilIcon } from "@heroicons/react/24/solid";
import Image from "next/image";

const ChatInterface: React.FC = () => {
  return (
    <div className="flex flex-col gap-6 bg-white p-6 rounded-lg max-w-7xl mx-auto">
      {/* Header */}
      <div className="text-right">
        <h2 className="text-2xl font-bold text-gray-900">تحدث عبر المحادثة</h2>
        <p className="text-gray-500 mt-1">
          اختر قدراتك مع قادر او اطرح عليه سؤال.
        </p>
      </div>

      {/* Layout: Sidebar & Chat */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Sidebar */}
        <div className="flex flex-col gap-4 col-span-1">
          {/* Card 1 */}
          <div className="bg-[#F5F7FA] p-4 rounded-xl flex flex-col items-center text-center">
            <div className="w-full h-24 bg-gray-300 rounded-lg mb-3 flex items-center justify-center">
              <Image
                src="/images/image-placeholder.png"
                alt="placeholder"
                width={100}
                height={100}
                className="object-contain"
              />
            </div>
            <h3 className="font-bold text-gray-800">اطرح سؤالك</h3>
            <p className="text-sm text-gray-500">اطرح سؤالك من هنا</p>
            <button className="bg-[#074182] hover:bg-[#053866] text-white text-sm mt-3 px-4 py-2 rounded-md flex items-center gap-1">
              <PencilIcon className="w-4 h-4" />
              ابدأ
            </button>
          </div>

          {/* Card 2 */}
          <div className="bg-[#F5F7FA] p-4 rounded-xl flex flex-col items-center text-center">
            <div className="w-full h-24 bg-gray-300 rounded-lg mb-3 flex items-center justify-center">
              <Image
                src="/images/image-placeholder.png"
                alt="placeholder"
                width={100}
                height={100}
                className="object-contain"
              />
            </div>
            <h3 className="font-bold text-gray-800">اختبر قدراتك</h3>
            <p className="text-sm text-gray-500">اختبر قدراتك من هنا</p>
            <button className="bg-[#074182] hover:bg-[#053866] text-white text-sm mt-3 px-4 py-2 rounded-md flex items-center gap-1">
              <PencilIcon className="w-4 h-4" />
              اختبرني
            </button>
          </div>
        </div>

        {/* Chat Panel */}
        <div className="col-span-2 flex flex-col justify-between rounded-xl border border-gray-200 p-4 min-h-[400px]">
          {/* Chat Empty State */}
          <div className="flex-1 flex flex-col justify-center items-center text-center text-gray-500">
            <Image
              src="/images/chat-empty.png"
              alt="no chat"
              width={150}
              height={150}
              className="mb-4"
            />
            <h3 className="font-bold text-gray-800 text-lg">لا توجد محادثات</h3>
            <p className="text-sm">اختر أحد الخيارات الجانبية للبدء!</p>
          </div>

          {/* Chat Input */}
          <div className="flex items-center gap-2 border-t pt-4 mt-4">
            <input
              type="text"
              placeholder="اكتب سؤالك هنا..."
              className="flex-1 border rounded-md px-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button className="bg-[#074182] hover:bg-[#053866] text-white px-4 py-2 rounded-md flex items-center gap-1">
              إرسال
              <PaperAirplaneIcon className="w-4 h-4" />
            </button>
            <button className="bg-gray-100 hover:bg-gray-200 p-2 rounded-md">
              <MicrophoneIcon className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
