"use client";
import React, { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

const mockData = [
  {
    date: "25/2/23",
    totalQuestions: 30,
    percentage: 90,
    verbal: "ممتاز",
    quantitative: "ممتاز",
    weakestSection: "لا يوجد",
    highlighted: true,
  },
  {
    date: "25/2/20",
    totalQuestions: 30,
    percentage: 90,
    verbal: "جيد جداً",
    quantitative: "ممتاز",
    weakestSection: "القسم اللفظي",
    highlighted: false,
  },
  {
    date: "25/2/18",
    totalQuestions: 30,
    percentage: 60,
    verbal: "ممتاز",
    quantitative: "ضعيف",
    weakestSection: "القسم الكمي",
    highlighted: false,
  },
];

const getBadgeColor = (level: string) => {
  switch (level) {
    case "ممتاز":
      return "bg-green-100 text-green-700";
    case "جيد جداً":
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
    setExpandedIndex(prev => (prev === index ? null : index));
  };

  return (
    <div className="w-full p-4">
      <h2 className="text-xl font-bold mb-4 text-right">سجل تجديد المستوى</h2>

      {/* Table for md and larger */}
      <div className="hidden md:block">
        <div className="overflow-x-auto border rounded-xl bg-white">
          <table className="min-w-full text-right text-sm">
            <thead className="bg-gray-100 text-gray-700 font-bold">
              <tr>
                <th className="p-4">التاريخ</th>
                <th className="p-4">عدد الأسئلة</th>
                <th className="p-4">النسبة</th>
                <th className="p-4">الأداء في القسم الكمي</th>
                <th className="p-4">الأداء في القسم اللفظي</th>
                <th className="p-4">أضعف قسم</th>
                <th className="p-4">لحظة الاختبار</th>
              </tr>
            </thead>
            <tbody>
              {mockData.map((item, i) => (
                <tr
                  key={i}
                  className={`border-b ${item.highlighted ? "bg-yellow-50 font-bold" : ""}`}
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
                  <td className="p-4">
                    <span className="text-sm text-gray-600">{item.weakestSection}</span>
                  </td>
                  <td className="p-4">
                    <button className="bg-white border border-blue-600 text-blue-600 px-4 py-2 rounded-md hover:bg-blue-50">
                      مراجعة الاختبار
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Collapsible Cards for small screens */}
      <div className="md:hidden flex flex-col gap-3">
        {mockData.map((item, i) => {
          const isOpen = expandedIndex === i;
          return (
            <div
              key={i}
              className={`bg-white border rounded-xl shadow-sm ${
                item.highlighted ? "border-yellow-400" : ""
              }`}
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
                    <strong>أضعف قسم:</strong> {item.weakestSection}
                  </div>
                  <button className="bg-white border border-blue-600 text-blue-600 w-full py-2 rounded-md hover:bg-blue-50">
                    مراجعة الاختبار
                  </button>
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
