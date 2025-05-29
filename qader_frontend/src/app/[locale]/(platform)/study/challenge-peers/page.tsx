'use client';
import React, { useState } from 'react';
import { PaperAirplaneIcon, ArrowPathIcon, XMarkIcon } from '@heroicons/react/24/solid';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import LoginModal from '@/components/challengeModel';
import Image from 'next/image';

const leaderboard = [
  { name: 'سلمان عبد', title: 'ثالث نادي', score: '20/20', online: true },
  { name: 'عبد أسعد', title: 'ثالث نادي', score: '20/20', online: false },
  { name: 'سامي العطيفي', title: 'ثالث نادي', score: '20/20', online: true },
  { name: 'باسم البسيالي', title: 'أول نادي', score: '20/20', online: false },
  { name: 'قاسم ناصر', title: 'ثالث نادي', score: '20/20', online: false },
  { name: 'انتصار', title: 'ثالث نادي', score: '20/20', online: false },
];

const history = [
  { name: 'عبد أسعد', date: '25/4/2025', title: 'ثالث نادي', score: '20/20' },
  { name: 'عبد أسعد', date: '25/4/2025', title: 'ثالث نادي', score: '20/20' },
  { name: 'سامي العطيفي', date: '25/4/2025', title: 'ثالث نادي', score: '20/20', online: true },
  { name: 'باسم البسيالي', date: '25/4/2025', title: 'أول نادي', score: '20/20' },
  { name: 'قاسم ناصر', date: '25/4/2025', title: 'ثالث نادي', score: '20/20' },
  { name: 'انتصار', date: '25/4/2025', title: 'ثالث نادي', score: '20/20' },
];

const WaitingModal = ({ username, onClose }: { username: string, onClose: () => void }) => {
  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-[110]" onClick={onClose} />
      <div className="fixed inset-0 z-[120] flex items-center justify-center">
        <div className="bg-white w-[350px] rounded-xl shadow-lg p-5 text-center relative">
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

export default function ChallengesSection() {
  const [showLogin, setShowLogin] = useState(false);
   const [username, setUsername] = useState('');

    const [showWaitingModal, setShowWaitingModal] = useState(false);
  
  
       const handleStartChallenge = () => {
     
        setShowWaitingModal(true);
      
    };

  const openLogin = () => {
    setShowLogin(true);
  };
  return (
    <div className="p-4 md:p-6 space-y-6 font-sans text-right">
      {/* عنوان القسم */}
      <div className="space-y-1">
        <h2 className="text-[20px] font-bold">تحدي الإملاء</h2>
        <p className="text-sm text-gray-600">تحدي زملائك واحصل على نقاط أكثر</p>
      </div>

      {/* زر تحدي جديد */}
      <div className="flex justify-between">
        <div>
          <p className='text-[20px] font-bold'>ابدأ تحدي جديد</p>
          <p className='text-sm text-gray-600'>تنافس مع زملائك على تحدي و اربح نقاط اكثر مقابل الفور</p>
        </div>
        <button onClick={openLogin} className="mt-4 flex justify-center gap-2 w-[180px] py-3 p-2 rounded-[8px] bg-[#074182] text-white font-semibold hover:bg-[#074182DF]">
          تحدي جديد
        </button>
      </div>

      {/* قائمة المتصدرين */}
      <Card className="border border-blue-300 rounded-xl">
        <CardContent className="p-4 space-y-4">
          <h3 className="text-md font-semibold">قائمة المتصدرين</h3>
          <div className="space-y-3">
            {leaderboard.map((user, i) => (
              <div key={i} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                {/* الصورة */}
                <div className="relative w-9 h-9 bg-gray-300 rounded-full">
                  {user.online && (
                    <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-white" />
                  )}
                </div>

                {/* الاسم والمستوى */}
                <div className="flex-1 text-sm text-gray-700">
                  <div className="font-semibold">{user.name}</div>
                  <div className="text-xs text-gray-500">{user.title}</div>
                </div>

                {/* النتيجة */}
                <div className="text-sm font-semibold text-gray-700">{user.score}</div>

                {/* زر التحدي */}
                <div className="flex items-center gap-2">
                  <div className="text-sm font-medium">تحدي شامل</div>
                  <button onClick={handleStartChallenge} className="w-9 h-9 rounded-lg bg-blue-800 text-white flex items-center justify-center">
                    <PaperAirplaneIcon className="h-4 w-4 rotate-180" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* سجل التحديات */}
      <Card className="border rounded-xl">
        <CardContent className="p-4 space-y-4">
          <h3 className="text-md font-semibold">سجل التحديات</h3>
          <div className="space-y-3">
            {history.map((entry, i) => (
              <div key={i} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                {/* الصورة */}
                <div className="relative w-9 h-9 bg-gray-300 rounded-full">
                  {entry.online && (
                    <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-green-500 rounded-full border-2 border-white" />
                  )}
                </div>

                {/* الاسم والمستوى */}
                <div className="flex-1 text-sm text-gray-700">
                  <div className="font-semibold">{entry.name}</div>
                  <div className="text-xs text-gray-500">{entry.title}</div>
                </div>

                {/* التاريخ */}
                <div className="text-sm font-semibold text-gray-700">{entry.date}</div>

                {/* النتيجة + زر التحديث */}
                <div className="flex items-center gap-2">
                  <div className="text-sm text-right">
                    <div className="font-medium">تحدي شامل</div>
                    <div className="text-xs font-bold">{entry.score}</div>
                  </div>
                  <button onClick={handleStartChallenge} className="w-9 h-9 rounded-lg bg-blue-800 text-white flex items-center justify-center">
                    <ArrowPathIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <LoginModal
        show={showLogin}
        onClose={() => setShowLogin(false)}
      />

       {showWaitingModal && <WaitingModal username={username} onClose={() => setShowWaitingModal(false)} />}
    </div>
  );
}
