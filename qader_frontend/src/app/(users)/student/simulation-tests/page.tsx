"use client";
import React, { useState, useEffect } from "react";
import { ChevronDown, ChevronUp, Repeat2, Eye, X } from "lucide-react";
import axios from "axios";

const defaultMockData = [
  {
    date: "2025-05-18T10:09:25.325Z",
    num_questions: 30,
    score_percentage: 90,
    performance: { verbal: "جيد", quantitative: "ممتاز" },
    weakestSection: "القواعد",
    highlighted: true,
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
  const [data, setData] = useState<any[]>([]);

  const toggleExpand = (index: number) => {
    setExpandedIndex((prev) => (prev === index ? null : index));
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem("accessToken");
        const response = await axios.get("https://qader.vip/ar/api/v1/study/attempts", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          params: {
            attempt_type: "simulation",
            status: "completed",
            ordering: "-date",
          },
        });

        if (response.data?.results?.length) {
          setData(response.data.results);
        } else {
          setData(defaultMockData);
        }
      } catch (error) {
        console.error("Failed to fetch attempt data", error);
        setData(defaultMockData);
      }
    };

    fetchData();
  }, []);

  const attemptList = data.length ? data : defaultMockData;

  return (
    <div className="w-full p-4 text-right">
      <div className="mb-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
        <h2 className="text-xl font-bold">اختبار المحاكاة</h2>
        <a href="/student/level/questions">
        <button className="bg-blue-900 text-white px-4 py-2 rounded-md text-sm flex items-center gap-2">
          <span>ابدأ اختبار جديد</span>
        </button>
        </a>
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

      <div className="hidden md:block overflow-x-auto border rounded-xl bg-white">
        <table className="min-w-full text-sm text-right">
          <thead className="bg-gray-100 text-gray-700 dark:bg-[#7E89AC]  dark:text-gray-200  font-bold">
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
            {attemptList.map((item, i) => (
              <tr
                key={i}
                className={`border-b dark:bg-[#0B1739] `}
              >
                <td className="p-4">{new Date(item.date).toLocaleDateString("en-EG")}</td>
                <td className="p-4">{item.num_questions} سؤال</td>
                <td className="p-4">{item.score_percentage}%</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-md text-xs ${getBadgeColor(item.performance?.quantitative ?? "")}`}>
                    {item.performance?.quantitative || "--"}
                  </span>
                </td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded-md text-xs ${getBadgeColor(item.performance?.verbal ?? "")}`}>
                    {item.performance?.verbal || "--"}
                  </span>
                </td>
                <td className="p-4 text-gray-500 text-sm">
                  {item.weakestSection || "--"}
                </td>
                <td className="p-4">
                   <a href="/student/level/questions/id">
                  <div className="flex items-center justify-center gap-4 mt-2"> 
                    <Repeat2 size={18} className="text-gray-500 cursor-pointer" />
                    <Eye size={18} className="text-gray-500 cursor-pointer" />
                    <X size={18} className="text-gray-500 cursor-pointer" />  
                  </div>
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="md:hidden flex flex-col gap-3 mt-4">
        {attemptList.map((item, i) => {
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
                  <span className="text-sm text-gray-500">{new Date(item.date).toLocaleDateString("ar-EG")}</span>
                  <span className="text-sm font-bold text-gray-800">{item.score_percentage}%</span>
                </div>
                {isOpen ? <ChevronUp className="text-gray-600" /> : <ChevronDown className="text-gray-600" />}
              </div>

              {isOpen && (
                <div className="px-4 pb-4 text-sm text-right">
                  <div className="mb-1 text-gray-700">
                    <strong>عدد الأسئلة:</strong> {item.num_questions} سؤال
                  </div>
                  <div className="mb-1">
                    <strong>القسم الكمي:</strong>{" "}
                    <span className={`px-2 py-1 rounded-md ${getBadgeColor(item.performance?.quantitative ?? "")}`}>
                      {item.performance?.quantitative || "--"}
                    </span>
                  </div>
                  <div className="mb-1">
                    <strong>القسم اللفظي:</strong>{" "}
                    <span className={`px-2 py-1 rounded-md ${getBadgeColor(item.performance?.verbal ?? "")}`}>
                      {item.performance?.verbal || "--"}
                    </span>
                  </div>
                  <div className="mb-2 text-gray-600">
                    <strong>أضعف قسم:</strong> {item.weakestSection || "--"}
                  </div>
                  <a href="/student/level/questions/id">
                  <div className="flex items-center justify-center gap-4 mt-2"> 
                    <Repeat2 size={18} className="text-gray-500 cursor-pointer" />
                    <Eye size={18} className="text-gray-500 cursor-pointer" />
                    <X size={18} className="text-gray-500 cursor-pointer" />  
                  </div>
                  </a>
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
