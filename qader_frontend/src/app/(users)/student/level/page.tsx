"use client";
import React, { useEffect, useState } from "react";
import Image from "next/image";
import { ChevronDown, ChevronUp } from "lucide-react";
import { PencilSquareIcon } from "@heroicons/react/24/solid";
import { Button } from "@/components/ui/button";
import axios from "axios";

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

const defaultMockData = [
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
    date: "25/2/23",
    totalQuestions: 30,
    percentage: 90,
    verbal: "ممتاز",
    quantitative: "ممتاز",
    weakestSection: "لا يوجد",
    highlighted: true,
  },
];

const LevelAssessmentPage = () => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
   const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  
    const toggleExpand = (index: number) => {
      setExpandedIndex(prev => (prev === index ? null : index));
    };

  const fetchAttempts = async () => {
    setLoading(true);
    try {
      const accessToken = localStorage.getItem("accessToken");

      const response = await axios.get("https://qader.vip/ar/api/v1/study/attempts", {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (response.data?.results?.length) {
        setData(response.data.results);
      }
    } catch (error: any) {
      if (error.response?.status === 401) {
        // Token might be expired, attempt refresh
        try {
          const refreshToken = localStorage.getItem("refreshToken");
          const refreshResponse = await axios.post("https://qader.vip/ar/api/v1/auth/token/refresh/", {
            refresh: refreshToken,
          });

          const newAccessToken = refreshResponse.data.access;
          localStorage.setItem("accessToken", newAccessToken);

          // Retry the original request with new token
          const retryResponse = await axios.get("https://qader.vip/ar/api/v1/study/attempts?attempt_type=level_assessment", {
            headers: {
              Authorization: `Bearer ${newAccessToken}`,
            },
          });

          if (retryResponse.data?.results?.length) {
            setData(retryResponse.data.results);
          }
        } catch (refreshError) {
          console.error("Token refresh failed", refreshError);
        }
      } else {
        console.error("API Error", error);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttempts();
  }, []);

  if (loading || data.length === 1) {
    return (
      <div className="flex min-h-screen dark:bg-[#081028] text-white">
        <div className="flex-1 flex items-center justify-center flex-col">
          <Image src="/images/search.png" width={100} height={100} alt="حدد مستواك" />
          <p className="font-semibold text-xl text-black dark:text-white mt-6">حدد مستواك</p>
          <p className="text-gray-500 w-[280px] text-center dark:text-[#D9E1FA]">
            اختبر مستواك معنا قبل البدء، ليتم بناء نموذج تعليمي شخصي لك يحدد نقاط القوة والضعف، بامكانك اعادة الاختبار اكثر من مرة.
          </p>
          <a href="/student/level/questions">
            <button className="mt-4 flex justify-center gap-2 w-[220px] py-3 p-2 rounded-[8px] bg-[#074182] text-white font-semibold hover:bg-[#074182DF]">
              <PencilSquareIcon className="w-5 h-5" />
              <span>ابدأ تحديد المستوى</span>
            </button>
          </a>
        </div>
      </div>
    );
  }

  return (
     <div className="w-full p-6 space-y-6 dark:bg-[#081028]">
      {/* Top header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="text-right space-y-1">
          <h2 className="text-2xl font-bold text-gray-800 dark:text-[#FDFDFD]">إعادة تحديد المستوى</h2>
          <p className="text-sm text-gray-500 dark:text-[#D9E1FA]">
            بإمكانك إعادة اختبار تحديد المستوى في أي وقت.
            <br />
            سيتم إعادة بناء نموذج مخصص لك مع زيادة عدد الاختبارات.
          </p>
        </div>
        <a href="/student/level/questions">
            <button className="mt-4 flex justify-center gap-2 w-[180px] py-3 p-2 rounded-[8px] bg-[#074182] text-white font-semibold hover:bg-[#074182DF]">
              <PencilSquareIcon className="w-5 h-5" />
              <span>ابدأ تحديد المستوى</span>
            </button>
          </a>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between bg-white dark:bg-[#0B1739] p-4 rounded-xl border text-sm">
  
  <div className="font-bold text-[18px] text-[#333333] dark:text-[#FDFDFD] text-right md:text-left">
    سجل تحديد المستوى
  </div>

  <div className="flex flex-col gap-4 md:flex-row md:items-center md:gap-6 w-full md:w-auto">
    
    {/* <label className="flex items-center gap-2 font-medium text-gray-700">
      <input type="checkbox" className="accent-blue-600" />
      عرض اختبارات الأداء الضعيف
    </label> */}
    
    <div className="flex flex-col md:flex-row md:items-center gap-2 md:gap-2 ">
      <label className="text-gray-700 font-semibold whitespace-nowrap dark:text-[#D9E1FA]">الفرز حسب</label>
      <select className="border rounded-md px-3 py-1 text-gray-700 dark:text-[#D9E1FA] dark:bg-[#0B1739]">
        <option>التاريخ الأحدث</option>
        <option>النسبة الأعلى</option>
      </select>
    </div>

  </div>
</div>

<div className="hidden md:block">
      <div className="overflow-x-auto bg-white border rounded-xl">
  <table className="min-w-full text-sm text-right text-gray-800">
    <thead className="bg-gray-50 font-bold text-gray-600 dark:bg-[#7E89AC] dark:text-[#FDFDFD]">
      <tr>
        <th className="p-4">التاريخ</th> 
        <th className="p-4">عدد الأسئلة</th>
        <th className="p-4">النسبة</th>
        <th className="p-4">الأداء في القسم الكمي</th>
        <th className="p-4">الأداء في القسم اللفظي</th>
        <th className="p-4">إعادة الاختبار</th>
      </tr>
    </thead>
    <tbody className=" ">
      {(data.length > 0 ? data : defaultMockData).map((item, i) => (
                <tr
                  key={i}
                  className={`border-b ${item.highlighted ? "bg-yellow-50 font-bold dark:bg-[#0B1739] dark:text-[#FDFDFD]" : "dark:bg-[#0B1739] dark:text-[#FDFDFD]"}`}
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
                    <button className=" flex justify-center gap-2 w-full  p-2 rounded-[8px] bg-[#074182] text-white font-semibold hover:bg-[#074182DF]">
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
            {(data.length > 0 ? data : defaultMockData).map((item, i) => {
              const isOpen = expandedIndex === i;
              return (
                <div
                  key={i}
                  className={`bg-white dark:bg-[#081028] border rounded-xl shadow-sm ${
                    item.highlighted ? "border-yellow-400" : ""
                  }`}
                >
                  <div
                    className="flex justify-between items-center p-4 cursor-pointer"
                    onClick={() => toggleExpand(i)}
                  >
                    <div className="flex flex-col text-right">
                      <span className="text-sm text-gray-500 dark:text-gray-100">{item.date}</span>
                      {/* <span className="text-sm font-bold text-gray-800">{item.percentage}%</span> */}
                    </div>
                    {isOpen ? <ChevronUp className="text-gray-600" /> : <ChevronDown className="text-gray-600" />}
                  </div>
    
                  {isOpen && (
                    <div className="px-4 pb-4 text-sm text-right dark:bg-[rgb(126,137,172)] py-3">
                      <div className="flex justify-center items-center gap-6 my-3">
                        <div className="mb-1 text-gray-700 dark:text-[#FDFDFD]">
                          <strong>عدد الأسئلة:</strong> {item.totalQuestions} سؤال
                        </div>
                        <div className="mb-1 text-gray-700 dark:text-[#FDFDFD]">
                          <strong>النسبة :</strong> {item.percentage}%
                        </div>
                      </div>
                      <div className="flex justify-center items-center gap-6 my-3">
                        <div className="mb-1 text-gray-700 dark:text-[#FDFDFD]">
                        <strong>القسم الكمي:</strong>{" "}
                        <span className={`px-2 py-1 rounded-md ${getBadgeColor(item.quantitative)}`}>
                          {item.quantitative}
                        </span>
                      </div>
                      <div className="mb-1 text-gray-700 dark:text-[#FDFDFD]">
                        <strong>القسم اللفظي:</strong>{" "}
                        <span className={`px-2 py-1 rounded-md ${getBadgeColor(item.verbal)}`}>
                          {item.verbal}
                        </span>
                      </div>
                      </div>
                      
                      <button className="mt-4 flex justify-center gap-2 w-full py-3 p-2 rounded-[8px] bg-[#074182] text-white font-semibold hover:bg-[#074182DF]">
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

export default LevelAssessmentPage;
