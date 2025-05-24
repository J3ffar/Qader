"use client";

import React, { useEffect, useState } from "react";
import axios from "axios";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { ClockIcon } from "@heroicons/react/24/outline";
import { BadgeCheck, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

interface TestResultOverviewProps {
  attemptId?: any;
}

const TestResultOverview: React.FC<TestResultOverviewProps> = ({ attemptId }) => {
  const [score, setScore] = useState(70);
  const [verbalScore, setVerbalScore] = useState(25);
  const [quantScore, setQuantScore] = useState(62);
  const router = useRouter();

  // Fallback ID for dev/test
  const id = attemptId ?? 1234;

  const pieData = [
    { name: "الكمي", value: quantScore, color: "#074182" },
    { name: "اللفظي", value: verbalScore, color: "#E6B11D" },
  ];

  useEffect(() => {
    const fetchReviewData = async () => {
      try {
        const token = localStorage.getItem("accessToken");
        const response = await axios.get(
          `https://qader.vip/ar/api/v1/study/attempts/${id}/review/`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        const data = response.data;
        setScore(data.score_percentage || 70);
        setVerbalScore(data.score_verbal || 25);
        setQuantScore(data.score_quantitative || 62);
      } catch (error) {
        console.error("Error fetching review data:", error);
      }
    };

    fetchReviewData();
  }, [id]);

  const handleRetake = async () => {
    try {
      const token = localStorage.getItem("accessToken");
      const response = await axios.post(
        `https://qader.vip/ar/api/v1/study/attempts/${id}/retake/`,
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const newAttemptId = response.data.attempt_id;
      router.push(`/student/level/questions/${newAttemptId}`);
    } catch (error) {
      console.error("Failed to retake test:", error);
    }
  };

  return (
    <div className="mx-auto p-4 space-y-6 bg-white shadow-md rounded-xl dark:bg-[#081028]">
      <h2 className="text-center text-lg font-bold text-gray-900 dark:text-white">
        نتيجتك في الاختبار جاهزة!
      </h2>

      {/* Score Display */}
      <div className="flex justify-center">
        <div className="bg-[#0D99FF] text-white font-bold py-2 px-6 rounded-full text-lg">
          {score}/100
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-center">
        <div className="border rounded-lg py-4 px-2 text-sm shadow-sm">
          <ClockIcon className="w-5 h-5 mx-auto text-gray-600 dark:text-gray-300" />
          <p className="text-gray-700 dark:text-gray-300 mt-1">الوقت المستغرق</p>
          <p className="font-bold text-[#0D99FF]">20 دقيقة</p>
        </div>
        <div className="border rounded-lg py-4 px-2 text-sm shadow-sm">
          <BadgeCheck className="w-5 h-5 mx-auto text-gray-600 dark:text-gray-300" />
          <p className="text-gray-700 dark:text-gray-300 mt-1">مستواك الحالي</p>
          <p className="font-bold text-[#E6B11D]">جيد</p>
        </div>
      </div>

      {/* Chart + Labels */}
      <div className="flex flex-col lg:flex-row items-center justify-center gap-6">
        <div className="w-full lg:w-1/2 h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                label={({ percent }) => `${(percent * 100).toFixed(0)}%`}
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="flex text-sm gap-6 justify-center items-center">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#074182]"></div>
          <p>الكمي - {quantScore}%</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-[#E6B11D]"></div>
          <p>اللفظي - {verbalScore}%</p>
        </div>
      </div>

      <div className="text-center">
        <p className="text-red-600 font-semibold mt-4">
          ينصح بمراجعة قسم القواعد اللفظية
        </p>
      </div>

      <div className="flex justify-center flex-wrap gap-4 mt-4">
        <a href={`/student/level/questions/${id}/results`}>
          <button className="flex justify-center items-center gap-2 min-[1120px]:py-3 min-[1120px]:px-4 p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer">
            مراجعة الاختبار
          </button>
        </a>
        <a href="/student/level/questions">
        <button
          onClick={handleRetake}
          className="flex justify-center items-center gap-2 min-[1120px]:py-2.5 min-[1120px]:px-4 p-2 rounded-[8px] bg-transparent border-[1.5px] border-[#074182] text-[#074182] dark:border-[#3D93F5] dark:text-[#3D93F5] font-[600] hover:bg-[#07418211] dark:hover:bg-[#3D93F511] transition-all cursor-pointer"
        >
          <RefreshCcw className="w-4 h-4 ml-2" />
          إعادة الاختبار
        </button>
        </a>
      </div>
    </div>
  );
};

export default TestResultOverview;
