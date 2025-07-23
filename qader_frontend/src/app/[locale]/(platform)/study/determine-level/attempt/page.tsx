"use client";
import React, { useState, useEffect } from "react";
import {
  PencilSquareIcon,
} from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

const TraditionalEdu = () => {
  const [isMounted, setIsMounted] = useState(false);
  const [checkedSections, setCheckedSections] = useState({
    section1: false,
    section2: false,
  });
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleToggle = (section: "section1" | "section2") => {
    setCheckedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handlePlus = () => setCount((prev) => prev + 1);
  const handleMinus = () => setCount((prev) => Math.max(0, prev - 1));

  const handleStartExam = async () => {
    const selectedSections: string[] = [];
    if (checkedSections.section1) selectedSections.push("quantitative");
    if (checkedSections.section2) selectedSections.push("verbal");
  
    if (selectedSections.length === 0 || count === 0) {
      alert("يرجى اختيار قسم واحد على الأقل وعدد أسئلة أكبر من 0.");
      return;
    }
  
    const token = localStorage.getItem("accessToken");
    if (!token) {
      alert("يجب تسجيل الدخول أولاً.");
      router.push("/"); // أو أي صفحة تسجيل دخول
      return;
    }
  
    setLoading(true);
    try {
      const res = await fetch("https://qader.vip/ar/api/v1/study/start/level-assessment/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          sections: selectedSections,
          num_questions: count,
        }),
      });
  
      const data = await res.json();
  
      // if (!res.ok) {
      //   alert(data.detail || "فشل بدء الاختبار");
      //   return;
      // }
  
      // حفظ البيانات في localStorage
      localStorage.setItem("level-questions", JSON.stringify(data.questions));
      localStorage.setItem("attemptId", String(data.attempt_id));
  
      // ✅ توجيه المستخدم إلى المسار الصحيح الجديد
      router.push(`/student/level/questions/${data.attempt_id}`);
      //  router.push(`/level/questions/1`);
    } catch (err) {
      console.error("فشل الاتصال:", err);
      alert("فشل الاتصال بالخادم.");
    } finally {
      setLoading(false);
    }
  };
  

  if (!isMounted) return null;

  return (
    <div className="p-5 space-y-8 dark:bg-[#081028]">
      <div className="text-center">
        <p className="font-bold text-xl">اختر الأقسام التي تريد التدريب عليها</p>
        <p className="text-gray-600 mt-2">اختر من بين الأقسام الأساسية والفرعية</p>
      </div>
 
      <div className="flex gap-6">
        {/* القسم الكمي */}
        <div
          className="flex-1 border rounded-2xl cursor-pointer"
          onClick={() => handleToggle("section1")}
        >
          <div className="flex items-center gap-2 bg-gray-100 rounded-t-2xl p-4 dark:bg-[#7E89AC]">
            <input
              type="checkbox"
              checked={checkedSections.section1}
              readOnly
              className="appearance-none w-5 h-5 rounded-full border border-gray-400 bg-white checked:bg-[#2f80ed] focus:outline-none cursor-pointer transition"
            />
            <p className="font-bold">القسم الكمي</p>
          </div>
          <div className="p-5 flex justify-center flex-wrap gap-3 dark:bg-[#0B1739] rounded-lg">
            {Array(5).fill("استيعاب المقروء").map((item, index) => (
              <p key={index} className="p-2 border w-fit rounded-lg">{item}</p>
            ))}
          </div>
        </div>

        {/* القسم اللفظي */}
        <div
          className="flex-1 border rounded-2xl cursor-pointer"
          onClick={() => handleToggle("section2")}
        >
          <div className="flex items-center gap-2 bg-gray-100 rounded-t-2xl p-4 dark:bg-[#7E89AC]">
            <input
              type="checkbox"
              checked={checkedSections.section2}
              readOnly
              className="appearance-none w-5 h-5 rounded-full border border-gray-400 bg-white checked:bg-[#2f80ed] focus:outline-none cursor-pointer transition"
            />
            <p className="font-bold">القسم اللفظي</p>
          </div>
          <div className="p-5 flex justify-center flex-wrap gap-3 rounded-lg dark:bg-[#0B1739]">
            {Array(5).fill("استيعاب المقروء").map((item, index) => (
              <p key={index} className="p-2 border w-fit rounded-lg">{item}</p>
            ))}
          </div>
        </div>
      </div>

      {/* التحكم في العد */}
      <div className="rounded-2xl bg-[#F0F0F0] dark:bg-[#0B1739] p-5 text-center">
        <p className="font-bold">عدد الأسئلة</p>
        <div className="flex justify-center items-center gap-6 mt-4">
          <button onClick={handleMinus} className="text-4xl text-[#0a60c2]">-</button>
          <span className="border border-[#0a60c2] px-5 py-2 rounded-lg">{count}</span>
          <button onClick={handlePlus} className="text-4xl text-[#0a60c2]">+</button>
        </div>
      </div>

      {/* زر بدء الاختبار */}
      <div className="flex justify-center">
        <button
          className="   flex justify-center gap-2 min-[1120px]:py-3 sm:w-[180px] w-[100px]  p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer"
          onClick={handleStartExam}
          disabled={loading}
        >
          <PencilSquareIcon className="w-6 h-6" />
          {loading ? "جارٍ بدء الاختبار..." : "ابدأ الاختبار"}
        </button>
      </div>
    </div>
  );
};

export default TraditionalEdu;
