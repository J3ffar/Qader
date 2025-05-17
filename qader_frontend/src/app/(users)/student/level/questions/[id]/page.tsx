"use client";
import React, { useState, useEffect } from "react";
import {
  ArrowRightEndOnRectangleIcon,
  CheckIcon,
} from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

// Default questions as a fallback
const defaultQuestions = [
  {
    text: "ما هو عاصمة فرنسا؟",
    options: ["باريس", "لندن", "روما", "مدريد"],
    correctAnswer: 0,
  },
  {
    text: "ما هي نتيجة 2 + 2؟",
    options: ["3", "4", "5", "6"],
    correctAnswer: 1,
  },
  {
    text: "ما هو لون السماء؟",
    options: ["أخضر", "أزرق", "أحمر", "أصفر"],
    correctAnswer: 1,
  },
  {
    text: "أي من هذه الحيوانات يطير؟",
    options: ["كلب", "قطة", "طائر", "سمكة"],
    correctAnswer: 2,
  },
  {
    text: "ما هو أكبر كوكب في النظام الشمسي؟",
    options: ["الأرض", "زحل", "المشتري", "نبتون"],
    correctAnswer: 2,
  },
];

const TraditionalEdu = () => {
  const [isMounted, setIsMounted] = useState(false);
  const [questions, setQuestions] = useState(defaultQuestions);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [userAnswers, setUserAnswers] = useState<(number | null)[]>([]);
  const [timeLeft, setTimeLeft] = useState(5 * 60 + 30); // 5 minutes 30 seconds
  const [isTimeOver, setIsTimeOver] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setIsMounted(true);

    // Fetch attempt data from API
    const fetchAttemptData = async () => {
      try {
        const response = await fetch("https://qader.vip/ar/api/v1/study/attempts/1/"); // Replace '1' with dynamic attempt_id if needed
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        const data = await response.json();
        if (data && data.results && data.results.length > 0) {
          // Map API data to match question structure
          const apiQuestions = data.results.map((item: any) => ({
            text: item.question_text,
            options: item.options,
            correctAnswer: item.correct_answer_index,
          }));
          setQuestions(apiQuestions);
        }
      } catch (error) {
        console.error("Failed to fetch attempt data:", error);
        // Keep default questions
      }
    };

    fetchAttemptData();

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setIsTimeOver(true);
          router.push("/student/level/questions/1/results");
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [router]);

  const formatTime = (seconds: number) => {
    const min = Math.floor(seconds / 60)
      .toString()
      .padStart(2, "0");
    const sec = (seconds % 60).toString().padStart(2, "0");
    return `${min}:${sec}`;
  };

  if (!isMounted) return null;

  const currentQuestion = questions[currentQuestionIndex];

  const handleConfirm = () => {
    if (selectedAnswer === null) return;

    const updatedAnswers = [...userAnswers];
    updatedAnswers[currentQuestionIndex] = selectedAnswer;
    setUserAnswers(updatedAnswers);
  };

  const handleNext = () => {
    if (selectedAnswer === null) return;

    const updatedAnswers = [...userAnswers];
    updatedAnswers[currentQuestionIndex] = selectedAnswer;
    setUserAnswers(updatedAnswers);

    setCurrentQuestionIndex((prev) => prev + 1);
    setSelectedAnswer(null);
  };

  const handleSubmit = () => {
    const updatedAnswers = [...userAnswers];
    updatedAnswers[currentQuestionIndex] = selectedAnswer;
    setUserAnswers(updatedAnswers);

    // Optionally, send userAnswers to the server here

    router.push("/student/level/questions/1/results");
  };

  const handleSelect = (index: number) => {
    if (isTimeOver) return;
    setSelectedAnswer(index);
  };

  return (
    <div className="p-5 dark:bg-[#081028]">
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div>
            <p className="font-bold text-lg">عنوان</p>
            <p className="text-gray-600 mt-1">وصف</p>
          </div>
          <button className="flex items-center gap-2 border border-[#f34b4b] p-2 rounded-lg text-[#f34b4b] font-semibold">
            <ArrowRightEndOnRectangleIcon className="w-5 h-5" />
            انهاء الاختبار
          </button>
        </div>

        {/* Progress */}
        <div className="flex items-center gap-4 mx-auto max-w-3xl">
          <div className="flex-1 bg-[#9ec9fa] rounded-full h-2 overflow-hidden">
            <div
              className="bg-[#074182] h-full"
              style={{
                width: `${((currentQuestionIndex + 1) / questions.length) * 100}%`,
              }}
            ></div>
          </div>
          <span className="text-[#074182]">
            {currentQuestionIndex + 1}/{questions.length}
          </span>
        </div>

        {/* Question Body */}
        <div className="flex flex-col lg:flex-row gap-8 mx-auto max-w-3xl">
          <div className="flex-1 space-y-6">
            <div className="border rounded-2xl">
              <div className="flex flex-wrap justify-between bg-[#074182] p-5 rounded-t-2xl text-white">
                <p className="font-semibold">اختر الإجابة الصحيحة</p>
                <div className="flex gap-2">
                  <button className="border py-1 px-3 rounded-md text-sm">⭐ تمييز</button>
                  <button className="border py-1 px-3 rounded-md text-sm">
                    ⏱ {formatTime(timeLeft)}
                  </button>
                </div>
              </div>
              <p className="p-5 font-bold text-gray-800 dark:text-gray-200 leading-7 border-b">
                {currentQuestion.text}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-5">
                {currentQuestion.options.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => handleSelect(index)}
                    disabled={isTimeOver}
                    className={`border border-[#074182] rounded-lg p-4 text-center ${
                      selectedAnswer === index
                        ? "bg-[#074182] text-white"
                        : "hover:bg-[#9ec9fa]"
                    } ${isTimeOver ? "opacity-50 cursor-not-allowed" : ""}`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>

            {/* Navigation Buttons */}
            <div className="flex justify-center gap-4 font-bold">
              {currentQuestionIndex < questions.length - 1 ? (
                <>
                  <Button
                    variant="outline"
                    className="flex items-center gap-2 py-6 px-8"
                    onClick={handleConfirm}
                    disabled={isTimeOver}
                  >
                    <CheckIcon className="w-5 h-5" /> تأكيد الإجابة
                  </Button>
                  <Button
                    variant="default"
                    className="py-6 px-8"
                    onClick={handleNext}
                    disabled={selectedAnswer === null || isTimeOver}
                  >
                    التالي
                  </Button>
                </>
              ) : (
                <Button
                  variant="default"
                  className="py-6 px-10"
                  onClick={handleSubmit}
                  disabled={selectedAnswer === null || isTimeOver}
                >
                  إرسال الإجابات
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TraditionalEdu;
