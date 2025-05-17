'use client';
import React from 'react';
import { PaperAirplaneIcon, ArrowPathIcon } from '@heroicons/react/24/solid';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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

export default function ChallengesSection() {
  return (
    <div className="p-4 md:p-6 space-y-6 font-sans text-right">
      {/* عنوان القسم */}
      <div className="space-y-1">
        <h2 className="text-lg font-bold">تحدي الإملاء</h2>
        <p className="text-sm text-gray-600">تحدي زملائك واحصل على نقاط أكثر</p>
      </div>

      {/* زر تحدي جديد */}
      <div className="flex justify-end">
        <Button className="bg-blue-700 text-white hover:bg-blue-800 text-sm px-4 py-1.5 rounded">
          تحدي جديد
        </Button>
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
                  <div className="w-9 h-9 rounded-lg bg-blue-800 text-white flex items-center justify-center">
                    <PaperAirplaneIcon className="h-4 w-4 rotate-180" />
                  </div>
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
                  <div className="w-9 h-9 rounded-lg bg-blue-800 text-white flex items-center justify-center">
                    <ArrowPathIcon className="h-4 w-4" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
