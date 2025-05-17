"use client";
import React, { useState } from "react";
import { ChevronDown, ChevronUp, Repeat2, Eye, X } from "lucide-react";

const mockData = [
  {
    date: "23/2/25",
    totalQuestions: 30,
    percentage: 90,
    verbal: "جيد",
    quantitative: "ممتاز",
    weakestSection: "",
    highlighted: true,
  },
  {
    date: "23/2/25",
    totalQuestions: 30,
    percentage: 90,
    verbal: "جيد",
    quantitative: "ممتاز",
    weakestSection: "",
    highlighted: false,
  },
  {
    date: "23/2/25",
    totalQuestions: 30,
    percentage: 90,
    verbal: "جيد",
    quantitative: "ممتاز",
    weakestSection: "",
    highlighted: false,
  },
  {
    date: "23/2/25",
    totalQuestions: 30,
    percentage: 90,
    verbal: "جيد",
    quantitative: "ممتاز",
    weakestSection: "",
    highlighted: false,
  },
  {
    date: "23/2/25",
    totalQuestions: 30,
    percentage: 90,
    verbal: "جيد",
    quantitative: "ممتاز",
    weakestSection: "",
    highlighted: false,
  },
  {
    date: "23/2/25",
    totalQuestions: 30,
    percentage: 90,
    verbal: "جيد",
    quantitative: "ممتاز",
    weakestSection: "",
    highlighted: false,
  },
];

const getBadgeColor = (level: string) => {
  switch (level) {
    case "ممتاز":
      return "bg-green-100 text-green-700";
    case "جيد جداً":
    case "جيد":
      return "bg-yellow-100 text-yellow-700";
    case "ضعيف":
      return "bg-red-100 text-red-700";
    default:
      return "bg-gray-100 text-gray-700";
  }
};

const LevelHistory = () => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const toggleExpand = (index: number) => {
    setExpandedIndex((prev) => (prev === index ? null : index));
  };

  return (
    <div className="w-full p-4 text-right">
      <div className="mb-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
        <h2 className="text-xl font-bold">اختبار المحاكاة</h2>
        <button className="bg-blue-900 text-white px-4 py-2 rounded-md text-sm flex items-center gap-2">
          <span>ابدأ اختبار جديد</span>
          <span className="text-xl">✏️</span>
        </button>
      </div>

      <div className="flex items-center justify-between flex-wrap gap-2 mb-2">
        <div className="flex items-center gap-2">
          <button className="border rounded-md px-2 py-1 text-sm text-gray-600 flex items-center gap-1">
            <span>التاريخ الأحدث</span>
            <ChevronDown size={16} />
          </button>
          <span className="text-sm text-gray-600">الفرز حسب</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">عرض اختبارات الأداء الضعيف</span>
          <input type="checkbox" className="toggle toggle-sm" />
        </div>
      </div>

      {/* Table */}
      <div className="hidden md:block overflow-x-auto border rounded-xl bg-white">
        <table className="min-w-full text-sm text-right">
          <thead className="bg-gray-100 text-gray-700 font-bold">
            <tr>
              <th className="p-4">التاريخ</th>
              <th className="p-4">عدد الأسئلة</th>
              <th className="p-4">النسبة</th>
              <th className="p-4">الأداء في القسم الكمي</th>
              <th className="p-4">الأداء في القسم اللفظي</th>
              <th className="p-4">أضعف قسم</th>
              <th className="p-4">إعادة الاختبار</th>
            </tr>
          </thead>
          <tbody>
            {mockData.map((item, i) => (
              <tr
                key={i}
                className={`border-b ${
                  item.highlighted ? "bg-gray-100 font-bold" : ""
                }`}
              >
                <td className="p-4">{item.date}</td>
                <td className="p-4">{item.totalQuestions} سؤال</td>
                <td className="p-4">{item.percentage}%</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-md text-xs ${getBadgeColor(item.quantitative)}`}>
                    {item.quantitative}
                  </span>
                </td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-md text-xs ${getBadgeColor(item.verbal)}`}>
                    {item.verbal}
                  </span>
                </td>
                <td className="p-4 text-gray-500 text-sm">
                  {item.weakestSection || "--"}
                </td>
                <td className="p-4">
                  <div className="flex items-center justify-center gap-2">
                    <Repeat2 size={18} className="text-gray-500 cursor-pointer" />
                    <Eye size={18} className="text-gray-500 cursor-pointer" />
                    <X size={18} className="text-gray-500 cursor-pointer" />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden flex flex-col gap-3 mt-4">
        {mockData.map((item, i) => {
          const isOpen = expandedIndex === i;
          return (
            <div
              key={i}
              className={`bg-white border rounded-xl shadow-sm ${item.highlighted ? "border-yellow-400" : ""}`}
            >
              <div
                className="flex justify-between items-center p-4 cursor-pointer"
                onClick={() => toggleExpand(i)}
              >
                <div className="flex flex-col text-right">
                  <span className="text-sm text-gray-500">{item.date}</span>
                  <span className="text-sm font-bold text-gray-800">{item.percentage}%</span>
                </div>
                {isOpen ? <ChevronUp className="text-gray-600" /> : <ChevronDown className="text-gray-600" />}
              </div>

              {isOpen && (
                <div className="px-4 pb-4 text-sm text-right">
                  <div className="mb-1 text-gray-700">
                    <strong>عدد الأسئلة:</strong> {item.totalQuestions} سؤال
                  </div>
                  <div className="mb-1">
                    <strong>القسم الكمي:</strong>{" "}
                    <span className={`px-2 py-1 rounded-md ${getBadgeColor(item.quantitative)}`}>
                      {item.quantitative}
                    </span>
                  </div>
                  <div className="mb-1">
                    <strong>القسم اللفظي:</strong>{" "}
                    <span className={`px-2 py-1 rounded-md ${getBadgeColor(item.verbal)}`}>
                      {item.verbal}
                    </span>
                  </div>
                  <div className="mb-2 text-gray-600">
                    <strong>أضعف قسم:</strong> {item.weakestSection || "--"}
                  </div>
                  <div className="flex items-center justify-center gap-4 mt-2">
                    <Repeat2 size={18} className="text-gray-500 cursor-pointer" />
                    <Eye size={18} className="text-gray-500 cursor-pointer" />
                    <X size={18} className="text-gray-500 cursor-pointer" />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default LevelHistory;