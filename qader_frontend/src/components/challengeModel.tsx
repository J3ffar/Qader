"use client";
import { XMarkIcon } from "@heroicons/react/24/solid";
import { EnvelopeIcon, LockClosedIcon } from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/button";

import React, { useState, useEffect } from 'react'
import { Facebook, Linkedin, Youtube, Instagram, Twitter, Send } from 'lucide-react';
import Image from "next/image";
import { GiftIcon } from '@heroicons/react/24/outline';

interface LoginModalProps {
  show: boolean;
  onClose: () => void;
  onSwitchToSignup?: () => void;
}

const challengeTypes = [
  { title: "تحدي الدقة", desc: "من يحقق أعلى نسبة دقة", icon: "/images/Group0.png" },
  { title: "لفظي متوسط", desc: "15 سؤال بدون تلميحات",icon: "/images/Group1.png" },
  { title: "كمّي سريع", desc: "10 أسئلة بوقت سريع",icon: "/images/Group2.png" },
  { title: "تحدي السرعة", desc: "من يحل أكثر خلال 5 دقائق",icon: "/images/Group3.png" },
  { title: "تحدي شامل", desc: "20 سؤال من أقسام مختلفة",icon: "/images/Group4.png" },
];


const WaitingModal = ({ username, onClose }: { username: string, onClose: () => void }) => {
  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-[110]" onClick={onClose} />
      <div className="fixed inset-0 z-[120] flex items-center justify-center">
        <div className="bg-white dark:bg-[#0B1739] w-[350px] rounded-xl shadow-lg p-5 text-center relative">
          <button onClick={onClose} className="absolute top-3 left-3 text-gray-500 hover:text-black">
            <XMarkIcon className="w-5 h-5" />
          </button>
          <h2 className="text-lg font-semibold text-[#074182] mb-4">اختر عشوائي</h2>
          <p className="text-sm font-medium mb-6">في انتظار التحدي...</p>
          <div className="flex justify-center items-center gap-4">
            <div className="text-center">
              <Image src="/images/user.png" alt="User" width={50} height={50} className="mx-auto rounded-full" />
              <p className="text-sm font-bold mt-2">{username || '---'}</p>
              <p className="text-xs text-gray-500">ثالث ثانوي</p>
            </div>
            <div className="h-12 w-px bg-gray-300" />
            <div className="text-center">
              <Image src="/images/question-mark.png" alt="Waiting" width={50} height={50} className="mx-auto rounded-full" />
              <p className="text-sm font-bold mt-2">؟</p>
              <p className="text-xs text-gray-500">ثالث ثانوي</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

const LoginModal: React.FC<LoginModalProps> = ({
  show,
  onClose,
  
}) => {
 
  const [activeSection, setActiveSection] = useState<"invite" | "store">("invite");
  const [username, setUsername] = useState('');
   const [selectedChallenge, setSelectedChallenge] = useState<number | null>(null);
    const [showWaitingModal, setShowWaitingModal] = useState(false);

     const canStart =
    (activeSection === 'invite' && username.trim() !== '' && selectedChallenge !== null) ||
    (activeSection === 'store' && selectedChallenge !== null);

     const handleStartChallenge = () => {
    if (canStart) {
      setShowWaitingModal(true);
    }
  };

  if (!show) return null;


  return (
    <>
      <div
        className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[100]"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
        <div
          className="relative w-full max-w-sm lg:max-w-3xl bg-background rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row"
          onClick={(e) => e.stopPropagation()}
        >
          <button
            onClick={onClose}
            className="absolute top-3 right-3 text-muted-foreground hover:text-foreground transition-colors z-10"
            aria-label="Close popup"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>

          <div className="w-full  flex items-center justify-center ">
            
        <div className=" w-full mx-auto  p-5  bg-white dark:bg-[#0B1739]">
          {/* الأقسام */}
          <div className="flex justify-between mb-5 ">
            <button
              onClick={() => setActiveSection("invite")}
              className={`flex-1 p-2 cursor-pointer border-b-1 ${activeSection === "invite" ? "text-[#074182] dark:text-[#3D93F5] dark:border-[#3D93F5] font-bold border-[#074182]" : "text-black border-black dark:text-[#FDFDFD] dark:border-[#FDFDFD]"}`}
            >
              دعوة صديق
            </button>
            <button
              onClick={() => setActiveSection("store")}
              className={`flex-1 p-2 cursor-pointer border-b-1 ml-2 ${activeSection === "store" ?  "text-[#074182] dark:text-[#3D93F5] dark:border-[#3D93F5] font-bold border-[#074182]" : "text-black border-black dark:text-[#FDFDFD] dark:border-[#FDFDFD]"}`}
            >
              اختيار عشوائي 
            </button>
          </div>

          {/* محتوى الأقسام */}
          {activeSection === "invite" && (
        //    <div className="fixed inset-0  bg-opacity-40 flex justify-center items-center z-50">
          <div className="bg-transparent mx-auto  w-full  rounded-xl py-5 space-y-4 relative text-right dark:bg-[#0B1739]">
            {/* <div className="text-lg font-bold text-white bg-[#074182] p-3 rounded-t-xl flex justify-between">
              <span>تحدي جديد</span>
              <button onClick={() => setShowPopup(false)} className="text-white">✕</button>
            </div> */}

           

            {/* Invite Tab */}
            {activeSection === 'invite' && (
              <>
                <div className="mt-4 mx-auto dark:bg-[#0B1739]">
                  <label className="text-sm font-medium text-gray-700">كود اسم المستخدم</label>
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="#rw283"
                    className="w-full p-2 mt-1 border rounded-md text-right"
                  />
                </div>
              </>
            )}

            {/* Challenge type selection */}
            <div className="mt-4 dark:bg-[#0B1739]">
              <p className="font-bold text-sm mb-2">اختر نوع التحدي</p>
              <div className="grid lg:grid-cols-5 sm:grid-cols-4 grid-cols-3 gap-4">
                {challengeTypes.map((type, index) => (
                  <div
                    key={index}
                    onClick={() => setSelectedChallenge(index)}
                    className={`border rounded-lg p-3 flex flex-col items-center text-center cursor-pointer transition-all ${selectedChallenge === index ? 'border-[#074182] shadow-lg' : ''}`}
                  >
                     <Image src={type.icon} alt={type.title} width={50} height={50} />
                    <p className="font-bold mt-2 text-sm">{type.title}</p>
                    <p className="text-xs text-gray-600 mt-1">{type.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Submit */}
            <div className="flex justify-center mt-6">
              <button
                disabled={!canStart}
                onClick={handleStartChallenge}
                className={`${canStart ? " flex justify-center rounded-[8px] bg-[#074182] text-white font-semibold hover:bg-[#074182DF]" : 'opacity-50 cursor-not-allowed rounded-[8px] bg-gray-300 text-white'} px-6 py-2`}
              >
                ابدأ التحدي
              </button>
            </div>
          </div>
        // </div>
          )}

          {activeSection === "store" && (
            <div>
               <div className="mt-4">
              <p className="font-bold text-sm mb-2">اختر نوع التحدي</p>
              <div className="grid lg:grid-cols-5 sm:grid-cols-4 grid-cols-3 gap-4">
                {challengeTypes.map((type, index) => (
                  <div
                    key={index}
                    onClick={() => setSelectedChallenge(index)}
                    className={`border rounded-lg p-3 flex flex-col items-center text-center cursor-pointer transition-all ${selectedChallenge === index ? 'border-[#074182] shadow-lg' : ''}`}
                  >
                     <Image src={type.icon} alt={type.title} width={50} height={50} />
                    <p className="font-bold mt-2 text-sm">{type.title}</p>
                    <p className="text-xs text-gray-600 mt-1">{type.desc}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex justify-center mt-6">
              <button
                disabled={!canStart}
                onClick={handleStartChallenge}
                 className={`${canStart ? " flex justify-center rounded-[8px] bg-[#074182] text-white font-semibold hover:bg-[#074182DF]" : 'opacity-50 cursor-not-allowed rounded-[8px] bg-gray-300 text-white'} px-6 py-2`}
              >
                ابدأ التحدي
              </button>
            </div>

            </div>
          )}

          {/* أيقونات المشاركة */}
          
        </div>
      
          </div>

          
        </div>
      </div>
      {showWaitingModal && <WaitingModal username={username} onClose={() => setShowWaitingModal(false)} />}
    </>
  );
};

export default LoginModal;
