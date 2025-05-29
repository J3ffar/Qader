"use client";
import React, { useState, useEffect } from "react";
import {
  ArrowRightEndOnRectangleIcon,
  CheckIcon,
} from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import axios from "axios";

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
  const [timeLeft, setTimeLeft] = useState(5 * 60 + 30);
  const [isTimeOver, setIsTimeOver] = useState(false);
  const [correctCount, setCorrectCount] = useState(0);
  const [wrongCount, setWrongCount] = useState(0);
  const [score, setScore] = useState(0);
  const router = useRouter();

  useEffect(() => {
    setIsMounted(true);

    const fetchAttemptData = async () => {
      try {
        const accessToken = localStorage.getItem("accessToken");
        const response = await axios.get("https://qader.vip/ar/api/v1/study/attempts/1/", {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        const data = response.data;
        if (data?.results?.length > 0) {
          const apiQuestions = data.results.map((item: any) => ({
            text: item.question_text,
            options: item.options,
            correctAnswer: item.correct_answer_index,
          }));
          setQuestions(apiQuestions);
        }
      } catch (error: any) {
        if (error.response?.status === 401) {
          try {
            const refreshToken = localStorage.getItem("refreshToken");
            const refreshResponse = await axios.post("https://qader.vip/ar/api/v1/auth/token/refresh/", {
              refresh: refreshToken,
            });

            const newAccessToken = refreshResponse.data.access;
            localStorage.setItem("accessToken", newAccessToken);

            const retryResponse = await axios.get("https://qader.vip/ar/api/v1/study/attempts/1/", {
              headers: {
                Authorization: `Bearer ${newAccessToken}`,
              },
            });

            const retryData = retryResponse.data;
            if (retryData?.results?.length > 0) {
              const apiQuestions = retryData.results.map((item: any) => ({
                text: item.question_text,
                options: item.options,
                correctAnswer: item.correct_answer_index,
              }));
              setQuestions(apiQuestions);
            }
          } catch (refreshError) {
            console.error("Token refresh failed", refreshError);
          }
        } else {
          console.error("Failed to fetch attempt data:", error);
        }
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
    const min = Math.floor(seconds / 60).toString().padStart(2, "0");
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

    const isCorrect = selectedAnswer === currentQuestion.correctAnswer;
    if (isCorrect) {
      setCorrectCount((prev) => prev + 1);
      setScore((prev) => prev + 2);
    } else {
      setWrongCount((prev) => prev + 1);
    }
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
    router.push("/student/level/questions/1/results");
  };

  const handleSelect = (index: number) => {
    if (isTimeOver) return;
    setSelectedAnswer(index);
  };

  return (
    <div className="p-5 dark:bg-[#081028]">
      <div className="space-y-8">
        <div className="flex flex-col md:flex-row justify-between items-center">
          <div>
            <p className="font-bold text-lg">عنوان</p>
            <p className="text-gray-600 mt-1">وصف</p>
          </div>
          <a href="/student/level">
            <button className="flex items-center gap-2 border border-[#f34b4b] p-2 rounded-lg text-[#f34b4b] font-semibold">
              <ArrowRightEndOnRectangleIcon className="w-5 h-5" />
              انهاء الاختبار
            </button>
          </a>
        </div>

        <div className="flex items-center gap-4 mx-auto max-w-3xl">
          <div className="flex-1 bg-[#9ec9fa] rounded-full h-2 overflow-hidden">
            <div
              className="bg-[#074182] h-full"
              style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
            ></div>
          </div>
          <span className="text-[#074182]">
            {currentQuestionIndex + 1}/{questions.length}
          </span>
        </div>

        <div className="flex flex-col lg:flex-row gap-8 mx-auto max-w-5xl">
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
                      selectedAnswer === index ? "bg-[#074182] text-white" : "hover:bg-[#9ec9fa]"
                    } ${isTimeOver ? "opacity-50 cursor-not-allowed" : ""}`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>

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

          <div className="border rounded-2xl w-full lg:w-2/5 bg-white shadow dark:bg-[#0B1739]">
            <div className="bg-[#074182] text-white rounded-t-2xl py-2 px-4 text-right">
              <p className="font-bold text-lg">خيارات متقدمة</p>
            </div>

            <div className="flex justify-around items-center text-center py-4 border-b">
              <div>
                <p className="text-red-600 font-bold text-xl">{wrongCount}</p>
                <p className="text-gray-600 text-sm">إجابة خاطئة</p>
              </div>
              <div>
                <p className="text-green-600 font-bold text-xl">{correctCount}</p>
                <p className="text-gray-600 text-sm">إجابة صحيحة</p>
              </div>
              <div>
                <p className="text-yellow-600 font-bold text-xl">{score}</p>
                <p className="text-gray-600 text-sm">النقاط المكتسبة</p>
              </div>
            </div>

            <div className="pt-4 text-center">
              <p className="text-sm font-bold mb-2 text-[#074182]">وسائل المساعدة</p>
              <div className="flex flex-col gap-2 px-4">
                <button className="border border-red-600 text-red-600 py-2 rounded-md">
                  حذف إجابة
                </button>
                <button className="border border-yellow-500 text-yellow-600 py-2 rounded-md">
                  اعطاء تلميح
                </button>
                <button className="border border-green-600 text-green-600 py-2 rounded-md">
                  عرض طريقة الحل
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TraditionalEdu;