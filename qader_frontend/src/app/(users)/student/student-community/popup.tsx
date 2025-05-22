"use client";

import React, { useState } from "react";
import { XMarkIcon, PaperClipIcon } from "@heroicons/react/24/outline";

interface PublishDiscussionModalProps {
  show: boolean;
  onClose: () => void;
}

const PublishDiscussionModal: React.FC<PublishDiscussionModalProps> = ({
  show,
  onClose,
}) => {
  const [content, setContent] = useState("");
  const [section, setSection] = useState("");

  if (!show) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/30 z-40"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Modal */}
      <div className="fixed inset-0 z-50 flex justify-center items-center p-4">
        <div className="bg-white rounded-lg w-full max-w-md shadow-lg border border-gray-200 relative">
          {/* Header */}
          <div className="flex justify-between items-center bg-[#074182] text-white px-4 py-3 rounded-t-lg">
            <h2 className="text-md font-bold">نشر مناقشة</h2>
            <button onClick={onClose}>
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="p-4 space-y-4 text-right">
            {/* User Info */}
            <div className="flex justify-end items-center gap-2">
              <div>
                <p className="text-sm font-bold text-gray-900">بيار سعيد</p>
                <p className="text-xs text-gray-500">ثالث ثانوي</p>
              </div>
              <div className="relative w-10 h-10 bg-gray-300 rounded-full">
                <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></span>
              </div>
            </div>

            {/* Label */}
            <label className="block text-sm font-bold text-gray-700">
              المناقشة
            </label>

            {/* Textarea */}
            <div className="relative">
              <textarea
                rows={6}
                className="w-full border rounded-md p-3 text-sm resize-none focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="اكتب نص مناقشتك هنا..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
              <PaperClipIcon className="absolute bottom-3 left-3 w-5 h-5 text-gray-400 cursor-pointer" />
            </div>

            {/* Dropdown */}
            <label className="block text-sm font-bold text-gray-700">
              حدد القسم
            </label>
            <select
              className="w-full border border-gray-300 rounded-md p-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
              value={section}
              onChange={(e) => setSection(e.target.value)}
            >
              <option value="">كمى</option>
              <option value="النقاشات الدراسية">النقاشات الدراسية</option>
              <option value="الاختبارات">الاختبارات</option>
              <option value="النصائح والتجارب">النصائح والتجارب</option>
              <option value="طلب زمالة">طلب زمالة</option>
              <option value="مسابقات شهرية">مسابقات شهرية</option>
            </select>

            {/* Submit */}
            <button
              className="bg-[#074182] hover:bg-[#053866] text-white py-2 px-4 rounded-md w-full font-bold mt-2"
              onClick={() => alert("✅ تم نشر المناقشة")}
            >
              نشر المناقشة
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default PublishDiscussionModal;
