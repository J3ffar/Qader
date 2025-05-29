"use client";
import React, { useState, useEffect } from "react";
import {
  PencilSquareIcon,
  ArrowRightEndOnRectangleIcon,
  ExclamationTriangleIcon,
  CheckIcon,
} from "@heroicons/react/24/outline";
import axios from "axios";
import { useRouter } from "next/navigation";

const TraditionalEdu = () => {
  const [isMounted, setIsMounted] = useState(false);
  const [checkedSections, setCheckedSections] = useState({
    section1: false,
    section2: false,
  });
  const [count, setCount] = useState(0);
  const [isActiveOne, setIsActiveOne] = useState(false);
  const [isActiveTwo, setIsActiveTwo] = useState(false);
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

  const handleStartTest = async () => {
    try {
      
      // const accessToken = localStorage.getItem("accessToken");
      // const selectedSubsections = [];

      // if (checkedSections.section1) selectedSubsections.push("القسم الكمى");
      // if (checkedSections.section2) selectedSubsections.push("القسم اللفظى");
      
      // const response = await axios.post(
      //   "https://qader.vip/ar/api/v1/study/start/traditional/",
      //   {
      //     subsections: selectedSubsections,
      //     skills: [],
      //     num_questions: count,
      //     starred: isActiveOne,
      //     not_mastered: isActiveTwo,
      //   },
      //   {
      //     headers: {
      //       Authorization: `Bearer ${accessToken}`,
      //       "Content-Type": "application/json",
      //     },
      //   }
      // );
      

      // const attemptId = response.data.attempt_id;
      router.push(`/student/traditional/1`);
    } catch (error) {
      console.error("Failed to start traditional practice test:", error);
    }
  };

  if (!isMounted) return null;

  return (
    <div className="p-5 dark:bg-[#081028]">
      <div className="one">
        <p className="font-bold">اختر الاقسام التى تريد التدريب عليها</p>
        <p className="text-gray-600">اختر من بين الاقسام الاساسية والفرعية</p>
        <div className="flex gap-5 mt-4">
          {/* القسم الكمي */}
          <div
            className="11 border rounded-2xl cursor-pointer"
            onClick={() => handleToggle("section1")}
          >
            <div className="flex gap-2 bg-gray-100 rounded-t-2xl p-4 dark:bg-[#7E89AC]">
              <input
                type="checkbox"
                checked={checkedSections.section1}
                onChange={() => {}}
                className="appearance-none w-5 h-5 rounded-full border border-gray-400 bg-white checked:bg-[#2f80ed] focus:outline-none cursor-pointer transition"
              />
              <p className="font-bold">القسم الكمى</p>
            </div>
            <div className="p-5 flex gap-3 flex-wrap max-md:flex-col">
              {[...Array(5)].map((_, idx) => (
                <p key={idx} className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
              ))}
            </div>
          </div>

          <div
            className="22 border rounded-2xl cursor-pointer"
            onClick={() => handleToggle("section2")}
          >
            <div className="flex gap-2 bg-gray-100 rounded-t-2xl p-4 dark:bg-[#7E89AC]">
              <input
                type="checkbox"
                checked={checkedSections.section2}
                onChange={() => {}}
                className="appearance-none w-5 h-5 rounded-full border border-gray-400 bg-white checked:bg-[#2f80ed] focus:outline-none cursor-pointer transition"
              />
              <p className="font-bold">القسم اللفظى</p>
            </div>
            <div className="p-5 flex gap-3 flex-wrap max-md:flex-col">
              {[...Array(5)].map((_, idx) => (
                <p key={idx} className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
              ))}
            </div>
          </div>
        </div>

        <p className="font-bold mt-4">خيارات متقدمة</p>
        <p className="text-gray-600">وصف وصف وصف وصف وصف وصف</p>
        <div className="flex gap-5 mt-4">
          <div className="border rounded-2xl cursor-pointer flex-1/2">
            <div className="flex gap-2 bg-gray-100 rounded-t-2xl p-4 dark:bg-[#7E89AC]">
              <p className="font-bold">عدد الاسئلة للتعلم</p>
            </div>
            <div className="p-5 flex justify-center items-center gap-3">
              <button onClick={handleMinus} className="text-4xl text-[#0a60c2] cursor-pointer">-</button>
              <span className="border-[#0a60c2] border p-3 rounded-lg cursor-default">{count}</span>
              <button onClick={handlePlus} className="text-xl text-[#0a60c2] cursor-pointer">+</button>
            </div>
          </div>

          <div className="border rounded-2xl cursor-pointer flex-1/2">
            <div className="flex gap-2 bg-gray-100 rounded-t-2xl p-4 dark:bg-[#7E89AC]">
              <p className="font-bold">الاسئلة المميزة بنجمة</p>
            </div>
            <div className="p-5 flex justify-center items-center gap-3">
              <div
                onClick={() => setIsActiveOne(!isActiveOne)}
                className={`w-12 h-6 rounded-full cursor-pointer flex items-center px-0.5 transition-colors duration-300 ${
                  isActiveOne ? "bg-blue-500" : "bg-gray-300"
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform duration-300 ${
                    isActiveOne ? "-translate-x-6" : "translate-x-0"
                  }`}
                ></div>
              </div>
            </div>
          </div>

          <div className="border rounded-2xl cursor-pointer flex-1/2">
            <div className="flex gap-2 bg-gray-100 rounded-t-2xl p-4 dark:bg-[#7E89AC]">
              <p className="font-bold">الاسئلة التى لم تتقنها</p>
            </div>
            <div className="p-5 flex justify-center items-center gap-3">
              <div
                onClick={() => setIsActiveTwo(!isActiveTwo)}
                className={`w-12 h-6 rounded-full cursor-pointer flex items-center px-0.5 transition-colors duration-300 ${
                  isActiveTwo ? "bg-blue-500" : "bg-gray-300"
                }`}
              >
                <div
                  className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform duration-300 ${
                    isActiveTwo ? "-translate-x-6" : "translate-x-0"
                  }`}
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-center mt-4">
          <button
            className="flex justify-center gap-2 bg-[#074182] text-white px-6 py-2 rounded-md font-semibold disabled:opacity-50"
            onClick={handleStartTest}
          >
            <PencilSquareIcon className="w-7 h-7 font-bold" />
            ابدأ الاختبار
          </button>
        </div>
      </div>
    </div>
  );
};

export default TraditionalEdu;
