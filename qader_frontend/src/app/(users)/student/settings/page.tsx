"use client"
import React, { useState } from 'react';

export default function SubscriptionSettings() {
  const [activeTab, setActiveTab] = useState<'current' | 'other'>('current');
  const [activePlan, setActivePlan] = useState<number>(1);

  const plans = [
    { id: 1, price: 75, period: 'شهرياً', features: ['الميزة ١', 'الميزة ٢', 'الميزة ٣', 'الميزة ٤'] },
    { id: 2, price: 75, period: 'كل 3 شهور', features: ['الميزة ١', 'الميزة ٢', 'الميزة ٣', 'الميزة ٤'] },
    { id: 3, price: 75, period: 'سنويًا', features: ['الميزة ١', 'الميزة ٢', 'الميزة ٣', 'الميزة ٤'] }
  ];

  return (
    <div className="p-8 bg-gray-50 text-right font-sans text-gray-800">
      {/* Header Tabs */}
      <div className="flex justify-end gap-4 mb-4">
        <button className="border px-4 py-1 rounded">الحساب</button>
        <button className="border-b-4 border-blue-600 font-semibold px-4 py-1 rounded text-blue-600">
          الاشتراكات
        </button>
      </div>

      {/* Title */}
      <div className="mb-8">
        <h2 className="text-lg font-bold mb-1">الاعدادات</h2>
        <p className="text-sm text-gray-500">تحكم في اعدادات حسابك على منصة فلان</p>
      </div>

      {/* Toggle Section */}
      <div className="bg-white p-4 rounded-lg mb-6">
        <h3 className="font-semibold mb-2">المرحلة الحالية</h3>
        <p className="text-sm text-gray-500 mb-4">هذه هي حزمة اشتراكك الحالية</p>

        <h3 className="font-semibold mt-4 mb-2">المرحلة الأخرى</h3>
        <p className="text-sm text-gray-500">تعرف على باقي الباقات المتوفرة لدينا</p>
      </div>

      {/* Tabs */}
      <div className="flex justify-center bg-gray-100 p-1 rounded-full w-64 mx-auto mb-8">
        <button
          onClick={() => setActiveTab('current')}
          className={`w-1/2 px-4 py-2 rounded-full text-sm font-medium ${
            activeTab === 'current' ? 'bg-white text-blue-600 shadow' : 'text-gray-500'
          }`}
        >
          الخطة
        </button>
        <button
          onClick={() => setActiveTab('other')}
          className={`w-1/2 px-4 py-2 rounded-full text-sm font-medium ${
            activeTab === 'other' ? 'bg-white text-blue-600 shadow' : 'text-gray-500'
          }`}
        >
          الباقة
        </button>
      </div>

      {/* Plans */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan, idx) => (
          <div
            key={plan.id}
            className={`bg-white p-6 rounded-xl shadow relative ${
              activePlan === idx ? 'border-2 border-orange-400 z-10' : ''
            }`}
          >
            {activePlan === idx && (
              <div className="absolute -top-4 right-4 bg-orange-500 text-white text-sm px-3 py-1 rounded-full shadow">
                الحزمة الحالية
              </div>
            )}
            <h4 className="text-sm font-semibold mb-1">حزمة البداية</h4>
            <p className="text-2xl font-bold text-gray-700 mb-1">
              {plan.price} <span className="text-sm font-normal text-gray-500">#</span>
            </p>
            <p className="text-sm text-gray-500 mb-4">{plan.period}</p>
            <button className="bg-blue-700 text-white w-full py-2 rounded mb-4">ترقية الباقة</button>
            <hr className="my-4" />
            <h5 className="font-semibold mb-2">الميزات</h5>
            <ul className="text-sm text-gray-600 space-y-1">
              {plan.features.map((f, i) => (
                <li key={i} className="flex items-center gap-2">
                  <span className="text-orange-500 text-xs">●</span> {f}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
