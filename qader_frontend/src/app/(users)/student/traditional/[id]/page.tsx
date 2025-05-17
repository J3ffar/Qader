"use client";
import React, { useState, useEffect } from "react";
import {
  PencilSquareIcon,
  ArrowRightEndOnRectangleIcon,
  ExclamationTriangleIcon,
  CheckIcon,
} from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/button";

const questions = [
  {
    type: "اختيار من متعدد",
    text: "ما هو عاصمة المملكة العربية السعودية؟",
    options: ["الرياض", "جدة", "مكة", "الدمام"],
    correctIndex: 0,
  },
  {
    type: "اختيار من متعدد",
    text: "ما هو ناتج 5 × 6؟",
    options: ["11", "30", "60", "56"],
    correctIndex: 1,
  },
  {
    type: "اختيار من متعدد",
    text: "أي من التالي كوكب؟",
    options: ["الشمس", "القمر", "زحل", "نجم البحر"],
    correctIndex: 2,
  },
  {
    type: "اختيار من متعدد",
    text: "من هو مؤسس شركة مايكروسوفت؟",
    options: ["مارك زوكربيرغ", "بيل غيتس", "ستيف جوبز", "إيلون ماسك"],
    correctIndex: 1,
  },
  {
    type: "اختيار من متعدد",
    text: "كم عدد أيام الأسبوع؟",
    options: ["5", "6", "7", "8"],
    correctIndex: 2,
  },
];

const TraditionalEdu = () => {
  const [isMounted, setIsMounted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [wrongCount, setWrongCount] = useState(0);
  const [score, setScore] = useState(0);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleConfirm = () => {
    const question = questions[currentQuestion];
    if (selectedOption === null) return;

    if (selectedOption === question.correctIndex) {
      setCorrectCount((prev) => prev + 1);
      setScore((prev) => prev + 2);
    } else {
      setWrongCount((prev) => prev + 1);
    }
  };

  const handleNext = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion((prev) => prev + 1);
      setSelectedOption(null);
    }
  };

  if (!isMounted) return null;

  const question = questions[currentQuestion];

  return (
    <div className="p-5 dark:bg-[#081028]">
      <div>
        <div className="flex justify-between">
          <div>
            <p className="font-bold">عنوان تحفيزى</p>
            <p className="text-gray-600 float-right">وصف</p>
          </div>
          <button className="flex items-center gap-3 border border-[#f34b4b] p-3 font-semibold rounded-lg text-[#f34b4b]">
            <ArrowRightEndOnRectangleIcon className="w-5 h-5" />
            انهاء التدريب
          </button>
        </div>

        <div className="flex justify-between gap-2 items-center mt-4 mx-40">
          <div className="bg-[#9ec9fa] w-full h-2 rounded-full overflow-hidden mr-4">
            <div
              className="bg-[#074182] h-full"
              style={{
                width: `${((currentQuestion + 1) / questions.length) * 100}%`,
              }}
            ></div>
          </div>
          <span className="text-sm font-bold text-blue-600">
            {currentQuestion + 1}/{questions.length}
          </span>
        </div>

        {/* Main Question Area */}
        <div className="two flex flex-col lg:flex-row gap-6 mt-4">
          {/* سؤال + خيارات */}
          <div>
            <div className="border rounded-2xl flex-1 pb-4">
              <div className="flex justify-between mb-4 flex-wrap gap-3 bg-[#074182] p-5 rounded-t-2xl">
                <p className="text-white font-semibold">{question.type}</p>
                <div className="flex gap-2">
                  <button className="border text-white py-2 px-4 rounded-md text-sm">
                    ⭐ تمييز
                  </button>
                  <span className="bg-gray-100 py-1 px-3 rounded-md text-sm flex items-center">
                    ⏱ 05:30
                  </span>
                  <button className="bg-yellow-400 text-white py-1 px-3 rounded-md text-sm flex items-center gap-2 font-semibold">
                    <ExclamationTriangleIcon className="w-5 h5" />
                    ابلاغ عن خطأ
                  </button>
                </div>
              </div>
              <p className="font-bold text-xl leading-8 text-gray-800 p-3 border-b border-gray-200">
                {question.text}
              </p>
              <div className="grid grid-cols-2 gap-4 mt-5 p-3">
                {question.options.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedOption(index)}
                    className={`border border-[#074182] rounded-lg p-4 text-center hover:bg-[#9ec9fa] ${
                      selectedOption === index ? "bg-[#9ec9fa]" : ""
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex justify-center gap-3 font-bold mt-5">
              <Button
                variant={"outline"}
                className="font-semibold py-6 px-9"
                onClick={handleConfirm}
              >
                <CheckIcon className="w-5 h-5" />
                تأكيد الاجابة
              </Button>
              <Button
                variant={"default"}
                className="font-semibold py-6 px-9"
                onClick={handleNext}
                disabled={currentQuestion === questions.length - 1}
              >
                التالي ←
              </Button>
            </div>
          </div>

          {/* نقاط ومساعدة */}
          <div className="border rounded-2xl w-full lg:w-2/5 bg-white shadow">
            <div className="bg-[#074182] text-white rounded-t-2xl py-2 px-4 text-right">
              <p className="font-bold text-lg">خيارات متقدمة</p>
            </div>

            <div className="flex justify-around items-center text-center py-4 border-b">
              <div>
                <p className="text-red-600 font-bold text-xl">{wrongCount}</p>
                <p className="text-gray-600 text-sm">إجابة خاطئة</p>
              </div>
              <div>
                <p className="text-green-600 font-bold text-xl">
                  {correctCount}
                </p>
                <p className="text-gray-600 text-sm">إجابة صحيحة</p>
              </div>
              <div>
                <p className="text-yellow-600 font-bold text-xl">{score}</p>
                <p className="text-gray-600 text-sm">النقاط المكتسبة</p>
              </div>
            </div>

            <div className="pt-4 text-center">
              <p className="text-sm font-bold mb-2 text-[#074182]">
                وسائل المساعدة
              </p>
              <div className="flex flex-col gap-2">
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
