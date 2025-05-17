"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { Button } from "@/components/ui/button";
import { CalendarDaysIcon } from "@heroicons/react/24/outline";

const performanceData = [
  { name: "J", general: 65, verbal: 40, quantitative: 70 },
  { name: "F", general: 70, verbal: 50, quantitative: 68 },
  { name: "M", general: 78, verbal: 60, quantitative: 60 },
  { name: "A", general: 85, verbal: 65, quantitative: 55 },
  { name: "M", general: 90, verbal: 68, quantitative: 50 },
  { name: "J", general: 88, verbal: 63, quantitative: 58 },
  { name: "A", general: 82, verbal: 60, quantitative: 64 },
  { name: "S", general: 84, verbal: 55, quantitative: 68 },
  { name: "O", general: 89, verbal: 58, quantitative: 72 },
  { name: "N", general: 91, verbal: 62, quantitative: 74 },
];

const pieData = [
  { name: "اللفظي", value: 35, color: "#00C49F" },
  { name: "الكمي", value: 40, color: "#FFBB28" },
  { name: "مستوى الأداء العام", value: 25, color: "#0088FE" },
];

const barData = [
  { name: "Sept 10", percent: 80 },
  { name: "Sept 11", percent: 60 },
  { name: "Sept 12", percent: 70 },
  { name: "Sept 13", percent: 50 },
  { name: "Sept 14", percent: 60 },
  { name: "Sept 15", percent: 90 },
  { name: "Sept 16", percent: 85 },
];

export default function StatsDashboard() {
  return (
    <div className="p-6 space-y-6 text-right">
      <h1 className="text-2xl font-bold">الإحصائيات</h1>

      {/* Summary boxes */}
      <div className="grid grid-cols-3 gap-4">
        {[
          {
            title: "التعلم بالطرق التقليدية",
            time: "10 ساعات",
            count: 50,
            level: "ممتاز",
            color: "text-green-600",
          },
          {
            title: "اختبار المحاكاة",
            time: "2 ساعات",
            count: 20,
            level: "ضعيف",
            color: "text-red-500",
          },
          {
            title: "تحديد المستوى",
            time: "1 ساعات",
            count: 10,
            level: "ممتاز",
            color: "text-green-600",
          },
        ].map((item, i) => (
          <div
            key={i}
            className="bg-white border p-4 rounded-xl space-y-1 shadow"
          >
            <div className="flex justify-between text-sm text-gray-500">
              <span>هذا الأسبوع</span>
              <CalendarDaysIcon className="w-5 h-5" />
            </div>
            <p className="font-semibold">{item.title}</p>
            <div className="flex items-center justify-between text-sm">
              <span>عدد المحاولات</span>
              <span className="font-bold">{item.count}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>الوقت المستغرق</span>
              <span className="font-bold">{item.time}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span>مستوى أدائك</span>
              <span className={`font-bold ${item.color}`}>{item.level}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Second row */}
      <div className="grid grid-cols-3 gap-4">
        {/* Notes */}
        <div className="bg-white border p-4 rounded-xl shadow">
          <h2 className="font-semibold mb-2">ملاحظات عامة</h2>
          <ul className="list-disc text-sm text-gray-600 pr-4 space-y-1">
            <li>تحتاج تحسين أداءك في اختبار المحاكاة.</li>
            <li>أنت بحاجة إلى مراجعة المفاهيم الأساسية.</li>
            <li>أنت بحاجة إلى تحسين التركيز.</li>
            <li>أنت بحاجة إلى زيادة عدد المحاولات.</li>
          </ul>
        </div>

        {/* Line Chart */}
        <div className="bg-white border p-4 rounded-xl shadow">
          <div className="flex justify-between text-sm text-gray-500 mb-1">
            <span>هذا الأسبوع</span>
            <span>تحسن الأداء</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={performanceData}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="general" stroke="#0088FE" />
              <Line type="monotone" dataKey="verbal" stroke="#00C49F" />
              <Line type="monotone" dataKey="quantitative" stroke="#FFBB28" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Pie Chart */}
        <div className="bg-white border p-4 rounded-xl shadow">
          <div className="flex justify-between text-sm text-gray-500 mb-1">
            <span>هذا الأسبوع</span>
            <span>نقاط القوة</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={70}
                label
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Legend />
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-3 gap-4">
        {/* Call to action */}
        <div className="bg-white border p-6 rounded-xl text-center shadow">
          <img
            src="/images/empty-chart.png"
            alt="جدول تحسين"
            className="mx-auto mb-4 w-24"
          />
          <p className="font-bold text-sm mb-2">ابني جدول لتحسين وضعك</p>
          <p className="text-gray-600 text-sm mb-4">
            دعنا نساعدك في بناء جدول مذاكرة لك لتحسين أدائك
          </p>
          <Button className="bg-blue-700 text-white px-6">ابني جدول</Button>
        </div>

        {/* Bar Chart */}
        <div className="col-span-2 bg-white border p-4 rounded-xl shadow">
          <div className="flex justify-between text-sm text-gray-500 mb-1">
            <span>هذا الشهر</span>
            <span>مقارنة الاختبارات</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData}>
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="percent" fill="#2f80ed" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

