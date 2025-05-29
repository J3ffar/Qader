'use client'
import React, { useState } from 'react';

export default function EmergencyModePanel() {
  const [hours, setHours] = useState(1);
  const [daysLeft, setDaysLeft] = useState(0);
  const [focusMode, setFocusMode] = useState(false);
  const [problemType, setProblemType] = useState('');
  const [problemDesc, setProblemDesc] = useState('');
 
  return (
    <div className="p-6 bg-gray-50 dark:bg-[#081028] min-h-screen text-gray-800">
      <h2 className="text-xl font-bold mb-2 text-center dark:text-gray-200">وضع الطوارئ</h2>
      <p className="text-center mb-6 text-sm text-gray-500">
        اختبارك قريبًا؟ متوتر وبدأت تضيع الوقت؟ على نفسك، فعل وضع الطوارئ
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Input Section */}
        <div className="bg-white p-6 dark:bg-[#0B1739] rounded-xl shadow">
          <h3 className="font-semibold mb-4 dark:text-gray-300">تفعيل وضع الطوارئ</h3>
          <div className="flex items-center justify-between mb-4 dark:text-gray-300">
            <label>كم ساعة تقدر تذاكر في اليوم</label>
            <div className="flex items-center gap-2">
              <button onClick={() => setHours(h => Math.max(0, h - 1))} className="px-3 py-1 border">-</button>
              <span>{String(hours).padStart(2, '0')} : 00</span>
              <button onClick={() => setHours(h => h + 1)} className="px-3 py-1 border">+</button>
            </div>
          </div>

          <div className="flex items-center justify-between mb-4 dark:text-gray-300">
            <label>كم يوم باقي للاختبار</label>
            <div className="flex items-center gap-2">
              <button onClick={() => setDaysLeft(d => Math.max(0, d - 1))} className="px-3 py-1 border">-</button>
              <span>{daysLeft}</span>
              <button onClick={() => setDaysLeft(d => d + 1)} className="px-3 py-1 border">+</button>
            </div>
          </div>

          <button className="w-full bg-blue-600 text-white py-2 rounded mt-4">تفعيل</button>
        </div>

        {/* Illustration and Message */}
        <div className="bg-white p-6 dark:bg-[#0B1739] rounded-xl shadow text-center flex flex-col justify-center items-center">
          <div className="text-6xl">📄</div>
          <h4 className="font-bold mt-4 dark:text-gray-300">حدد عدد الأيام و الساعات</h4>
          <p className="text-sm text-gray-500 mt-2">
            تحتاج لتحديد عدد الأيام الباقية للاختبار وعدد الساعات اللي تستطيع المذاكرة فيها لتفعيل وضع الطوارئ
          </p>
        </div>

        {/* Problem Report Section */}
        <div className="bg-white p-6 dark:bg-[#0B1739] rounded-xl shadow">
          <h3 className="font-semibold mb-4 dark:text-gray-300">مشاركة وضعي مع الإدارة</h3>
          <p className="text-sm text-gray-500 mb-4">
            شارك مشكلتك! ونحتاج دعم أملاك؟ شاركنا الوضع واطلب الاقتراح.
          </p>
          <div className="mb-4">
            <label className="block mb-1 dark:text-gray-300">نوع المشكلة</label>
            <select
              className="w-full border rounded px-3 py-2"
              value={problemType}
              onChange={(e) => setProblemType(e.target.value)}
            >
              <option className=' dark:text-gray-300' value="">-- اختر --</option>
              <option className=' dark:text-gray-300' value="نفسية">نفسية</option>
              <option className=' dark:text-gray-300' value="تنظيم الوقت">تنظيم الوقت</option>
              <option className=' dark:text-gray-300' value="ضغط الدراسة">ضغط الدراسة</option>
            </select>
          </div>
          <div className="mb-4">
            <label className="block mb-1 dark:text-gray-300">وصف الطلب</label>
            <textarea
              className="w-full border rounded px-3 py-2"
              rows={4}
              placeholder="اكتب مشكلتك..."
              value={problemDesc}
              onChange={(e) => setProblemDesc(e.target.value)}
            />
          </div>
          <button className="w-full bg-blue-600 text-white py-2 rounded">إرسال</button>
        </div>

        {/* Focus Mode Tips Section */}
        <div className="bg-white p-6 dark:bg-[#0B1739] rounded-xl shadow">
          <div className="flex justify-between items-center mb-4 dark:text-gray-300">
            <span>هل تريد تفعيل الوضع السري للتركيز أكثر؟</span>
            <label className="inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                className="sr-only peer"
                checked={focusMode}
                onChange={() => setFocusMode(!focusMode)}
              />
              <div className="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-blue-600 relative">
                <div className="dot absolute top-1 left-1 w-4 h-4 bg-white rounded-full transition peer-checked:translate-x-5"></div>
              </div>
            </label>
          </div>
          <h4 className="font-semibold mb-2 dark:text-gray-300">نصائح عامة لك</h4>
          <ul className="text-sm text-gray-500 list-disc pl-5 space-y-1">
            <li>نصائح التقليل من التوتر</li>
            <li>نصيحة ٢</li>
            <li>نصيحة ٣</li>
            <li>نصيحة ٤</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
