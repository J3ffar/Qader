"use client";
import React, { useEffect, useState } from "react";
import {
  ChevronDownIcon,
  ChevronUpIcon,
  ArrowRightEndOnRectangleIcon,
} from "@heroicons/react/24/outline";
import axios from "axios";

const defaultQuestionsData = [
  {
    question_id: 1,
    question: "ما هو عاصمة مصر؟",
    options: ["القاهرة", "الرباط", "تونس", "دمشق"],
    correctAnswer: 0,
  },
  {
    question_id: 2,
    question: "من هو مؤسس شركة آبل؟",
    options: ["إيلون ماسك", "ستيف جوبز", "بيل غيتس", "مارك زوكربيرغ"],
    correctAnswer: 1,
  },
  {
    question_id: 3,
    question: "ما هو أكبر محيط في العالم؟",
    options: ["الأطلسي", "الهندي", "الهادي", "المتجمد الشمالي"],
    correctAnswer: 2,
  },
  {
    question_id: 4,
    question: "كم عدد كواكب المجموعة الشمسية؟",
    options: ["7", "8", "9", "10"],
    correctAnswer: 1,
  },
  {
    question_id: 5,
    question: "ما هي عاصمة اليابان؟",
    options: ["سيول", "طوكيو", "بكين", "بانكوك"],
    correctAnswer: 1,
  },
];

const attempt_id = 1234; // Replace with actual attempt ID

const TestResults = () => {
  const [isMounted, setIsMounted] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [apiAnswers, setApiAnswers] = useState<Record<number, any>>({});

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    const fetchAnswer = async () => {
      const question = defaultQuestionsData[currentQuestionIndex];
      if (!question || apiAnswers[question.question_id]) return;

      try {
        const response = await axios.get(
          `https://qader.vip/ar/api/v1/study/attempts/${attempt_id}/answer/`,
          {
            params: {
              question_id: question.question_id,
            },
          }
        );

        setApiAnswers((prev) => ({
          ...prev,
          [question.question_id]: response.data,
        }));
      } catch (error) {
        console.warn("API fallback to default data for question", question.question_id);
      }
    };

    fetchAnswer();
  }, [currentQuestionIndex]);

  if (!isMounted) return null;

  const currentQuestion = defaultQuestionsData[currentQuestionIndex];
  const apiData = apiAnswers[currentQuestion.question_id];

  const correctAnswerIndex = apiData
    ? currentQuestion.options.findIndex((opt) => opt === apiData.correct_answer)
    : currentQuestion.correctAnswer;

  return (
    <div className="p-5 dark:bg-[#081028]">
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <div>
            <p className="font-bold text-lg">نتيجة الاختبار</p>
            <p className="text-gray-600 mt-1">شاهد الإجابات الصحيحة لكل سؤال</p>
          </div>
          <a href="/student/level/questions/1/score">
            <button className="flex items-center gap-2 border border-[#f34b4b] p-2 rounded-lg text-[#f34b4b] font-semibold">
            <ArrowRightEndOnRectangleIcon className="w-5 h-5" />
            عرض النتائج
          </button>
          </a>
        </div>

        <div className="flex flex-col md:flex-row-reverse min-h-screen p-4 gap-4 ">
          {/* Sidebar */}
          <div className="md:w-1/4 ">
            <div className="block md:hidden ">
              <button
                className="w-full bg-[#074182] text-white p-3 rounded-md flex justify-between items-center"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                <span>جميع الأسئلة</span>
                {sidebarOpen ? <ChevronUpIcon className="w-5 h-5" /> : <ChevronDownIcon className="w-5 h-5" />}
              </button>

              {sidebarOpen && (
                <div className="bg-white border rounded-b-md mt-2 p-3 dark:bg-[#081028]">
                  <p className="text-center font-bold text-lg mb-4 ">5 أسئلة</p>
                  <div className="grid grid-cols-5 gap-2">
                    {defaultQuestionsData.map((_, i) => (
                      <button
                        key={i}
                        className={`border rounded-full w-8 h-8 text-sm flex items-center justify-center ${
                          i === currentQuestionIndex ? "bg-[#074182] text-white" : ""
                        }`}
                        onClick={() => setCurrentQuestionIndex(i)}
                      >
                        {i + 1}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="hidden md:flex flex-col bg-white border rounded-xl h-full dark:bg-[#0B1739]">
              <p className="w-full h-[60px] flex items-center bg-[#074182] dark:bg-[#081028] rounded-tl-xl rounded-tr-xl px-4 text-[18px] font-[700] text-[#FDFDFD]">
                جميع الأسئلة
              </p>
              <p className="text-center font-bold text-2xl text-[#E6B11D] mt-5">5</p>
              <p className="text-center mb-4 text-[#4F4F4F] dark:text-gray-200">سؤال</p>
              <div className="grid grid-cols-5 gap-2 px-4 pb-4 ">
                {defaultQuestionsData.map((_, i) => (
                  <button
                    key={i}
                    className={`border border-[#074182] dark:border-[#3D93F5] rounded-[8px] w-8 h-8 text-sm flex items-center justify-center ${
                      i === currentQuestionIndex ? "bg-[#074182] text-white" : "text-[#074182] dark:text-[#3D93F5]"}
                    `}
                    onClick={() => setCurrentQuestionIndex(i)}
                  >
                    {i + 1}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 flex flex-col bg-white border rounded-xl dark:bg-[#0B1739]">
            <div className="border rounded-md overflow-hidden mb-6">
              <div className="bg-[#074182] dark:text-gray-200 dark:bg-[#081028] text-white p-4 font-semibold">سؤال {currentQuestionIndex + 1}</div>
              <div className="p-4 text-gray-800 dark:text-gray-200 font-bold text-[20px] leading-relaxed dark:bg-[#0B1739]">
                {currentQuestion.question}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6 px-4 dark:text-gray-200">
              {currentQuestion.options.map((option, index) => {
                const isCorrect = index === correctAnswerIndex;
                const btnClass = isCorrect
                  ? "bg-[#27AE60] text-white border rounded-md p-4 dark:text-gray-200"
                  : "text-[#0E1825] border rounded-md p-4 dark:text-gray-200";

                return (
                  <div key={index} className={btnClass}>
                    {option}
                  </div>
                );
              })}
            </div>

            <div className="px-4">
              <h3 className="font-bold text-[20px] text-[#333333] mb-2 dark:text-gray-200">الإجابة الصحيحة:</h3>
              <p className="text-gray-700 text-[18px]">
                <span className="text-green-600 font-bold">✔ {currentQuestion.options[correctAnswerIndex]}</span>
              </p>
              {apiData?.explanation && (
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-300">{apiData.explanation}</p>
              )}
            </div>

            <div className="flex justify-center gap-6 mt-8">
              <button
                onClick={() => setCurrentQuestionIndex((prev) => Math.max(prev - 1, 0))}
                className="bg-[#074182] text-white px-6 py-2 rounded-md font-semibold disabled:opacity-50"
                disabled={currentQuestionIndex === 0}
              >
                السابق
              </button>
              <button
                onClick={() => setCurrentQuestionIndex((prev) => Math.min(prev + 1, defaultQuestionsData.length - 1))}
                className="bg-[#074182] text-white px-6 py-2 rounded-md font-semibold disabled:opacity-50"
                disabled={currentQuestionIndex === defaultQuestionsData.length - 1}
              >
                التالي
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestResults;