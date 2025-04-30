"use client"
import React, { useState, useEffect } from 'react'
import { Facebook, Linkedin, Youtube, Instagram, Twitter, Send } from 'lucide-react';
import Image from "next/image";
import { GiftIcon } from '@heroicons/react/24/outline';

const GiftContain = ({ isVisible, activeSection, setActiveSection }: { 
  isVisible: boolean; 
  activeSection: "invite" | "store";
  setActiveSection: (section: "invite" | "store") => void;
}) => {
  const [isClient, setIsClient] = useState(false);

  // To ensure that we only run the logic on the client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) {
    return null; // Do not render anything on the server side
  }

  return (
    <div>
      {isVisible && (
        <div className="giftcontain absolute top-1 left-3 w-full max-w-md mx-auto mt-[80px] p-5 border rounded-lg shadow-md bg-white">
          {/* الأقسام */}
          <div className="flex justify-between mb-5">
            <button
              onClick={() => setActiveSection("invite")}
              className={`flex-1 p-2 cursor-pointer border-b-1 ${activeSection === "invite" ? "text-[#074182] font-bold border-[#074182]" : "text-black border-black"}`}
            >
              دعوة صديق
            </button>
            <button
              onClick={() => setActiveSection("store")}
              className={`flex-1 p-2 cursor-pointer border-b-1 ml-2 ${activeSection === "store" ? "text-[#074182] font-bold border-[#074182]" : "text-black border-black"}`}
            >
              المتجر
            </button>
          </div>

          {/* محتوى الأقسام */}
          {activeSection === "invite" && (
            <div>
              <p className="text-lg font-semibold mb-1">احصل على 3 أيام مجانية مقابل دعوة صديق</p>
              <p className="text-gray-600 mb-5">قم بمشاركة رابط المنصة للحصول على 3 أيام مجانية</p>
              <div className="bg-[#e7f1fe] border border-[#9ec9fa] p-7 rounded-2xl flex gap-5 items-center">
                <span className="w-9 h-9 rounded-xl bg-[#9ec9fa] flex justify-center items-center">
                  <GiftIcon className="w-6 h-6 text-[#074182] font-bold" />
                </span>
                <span className="flex flex-col">
                  <span className="text-gray-600 ml-20">رابط الدعوة</span>
                  <a href="https://www.qader.vip" className="text-black underline break-all">
                    https://www.qader.vip
                  </a>
                </span>
              </div>
            </div>
          )}

          {activeSection === "store" && (
            <div>
              <p className="text-lg font-semibold mb-1">عرض مميز لك لاستبدال نقاطك</p>
              <p className="text-gray-600 mb-5">لا يوجد عرض خاص لك حتى الآن، قم بإجراء أي نشاط للحصول على عروض</p>
              <div className="bg-[#e7f1fe] border border-[#9ec9fa] p-7 rounded-2xl flex flex-col items-center gap-1">
                <Image src="/images/gift.png" width={50} height={50} alt="هدية" />
                <p className="font-bold">لا توجد عروض خاصة</p>
                <p className="text-gray-500 text-center">سيتم إبلاغك عبر الإشعارات في حال تواجد عروض خاصة لك.</p>
              </div>
            </div>
          )}

          {/* أيقونات المشاركة */}
          <div className="flex gap-3 justify-center items-center mt-5">
            <span className="w-8 h-8 flex items-center justify-center rounded-full bg-[#074182]">
              <Send className="w-4 h-4 text-white" />
            </span>
            <span className="w-8 h-8 flex items-center justify-center rounded-full bg-[#074182]">
              <Facebook className="w-4 h-4 text-white" />
            </span>
            <span className="w-8 h-8 flex items-center justify-center rounded-full bg-[#074182]">
              <Linkedin className="w-4 h-4 text-white" />
            </span>
            <span className="w-8 h-8 flex items-center justify-center rounded-full bg-[#074182]">
              <Youtube className="w-4 h-4 text-white" />
            </span>
            <span className="w-8 h-8 flex items-center justify-center rounded-full bg-[#074182]">
              <Instagram className="w-4 h-4 text-white" />
            </span>
            <span className="w-8 h-8 flex items-center justify-center rounded-full bg-[#074182]">
              <Twitter className="w-4 h-4 text-white" />
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default GiftContain;
