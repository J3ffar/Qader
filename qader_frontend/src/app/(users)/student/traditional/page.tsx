"use client";
import React, { useState, useEffect } from "react";
import { PencilSquareIcon,ArrowRightEndOnRectangleIcon, ExclamationTriangleIcon,CheckIcon} from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/button";

const TraditionalEdu = () => {
  const [isMounted, setIsMounted] = useState(false);
  const [checkedSections, setCheckedSections] = useState({
    section1: false,
    section2: false,
  });
  const [count, setCount] = useState(0);
  const [isActiveOne, setIsActiveOne] = useState(false);
  const [isActiveTwo, setIsActiveTwo] = useState(false);
  const [started, setStarted] = useState(false); // ✅ الحالة الخاصة ببداية الاختبار

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const handleToggle = (section: "section1" | "section2") => {
    setCheckedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handlePlus = () => {
    setCount((prev) => prev + 1);
  };

  const handleMinus = () => {
    setCount((prev) => Math.max(0, prev - 1));
  };

  if (!isMounted) return null;

  return (
    <div className="p-5">
      {/* ✅ الجزء الأول يظهر فقط قبل بدء الاختبار */}
      {!started && (
        <div className="one">
          <p className="font-bold">اختر الاقسام التى تريد التدريب عليها</p>
          <p className="text-gray-600">اختر من بين الاقسام الاساسية والفرعية</p>
          <div className="flex gap-5 mt-4">
            {/* القسم الكمي */}
            <div
              className="11 border rounded-2xl cursor-pointer"
              onClick={() => handleToggle("section1")}
            >
              <div className="flex gap-2 bg-gray-100 rounded-t-2xl p-4">
                <input
                  type="checkbox"
                  checked={checkedSections.section1}
                  onChange={() => {}}
                  className="appearance-none w-5 h-5 rounded-full border border-gray-400 bg-white checked:bg-[#2f80ed] focus:outline-none cursor-pointer transition"
                />
                <p className="font-bold">القسم الكمى</p>
              </div>
              <div className="p-5 flex gap-3 flex-wrap max-md:flex-col">
                <p className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
                <p className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
                <p className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
                <p className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
                <p className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
              </div>
            </div>

            {/* القسم اللفظي */}
            <div
              className="22 border rounded-2xl cursor-pointer"
              onClick={() => handleToggle("section2")}
            >
              <div className="flex gap-2 bg-gray-100 rounded-t-2xl p-4">
                <input
                  type="checkbox"
                  checked={checkedSections.section2}
                  onChange={() => {}}
                  className="appearance-none w-5 h-5 rounded-full border border-gray-400 bg-white checked:bg-[#2f80ed] focus:outline-none cursor-pointer transition"
                />
                <p className="font-bold">القسم اللفظى</p>
              </div>
              <div className="p-5 flex gap-3 flex-wrap max-md:flex-col">
                <p className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
                <p className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
                <p className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
                <p className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
                <p className="p-2 border w-fit rounded-lg">استيعاب المقروء</p>
              </div>
            </div>
          </div>

          <p className="font-bold mt-4">خيارات متقدمة</p>
          <p className="text-gray-600">وصف وصف وصف وصف وصف وصف</p>
          <div className="flex gap-5 mt-4">
            <div className="border rounded-2xl cursor-pointer flex-1/2">
              <div className="flex gap-2 bg-gray-100 rounded-t-2xl p-4">
                <p className="font-bold">عدد الاسئلة للتعلم</p>
              </div>
              <div className="p-5 flex justify-center items-center gap-3">
                <button
                  onClick={handleMinus}
                  className="text-4xl text-[#0a60c2] cursor-pointer"
                >
                  -
                </button>
                <span className="border-[#0a60c2] border p-3 rounded-lg cursor-default">
                  {count}
                </span>
                <button
                  onClick={handlePlus}
                  className="text-xl text-[#0a60c2] cursor-pointer"
                >
                  +
                </button>
              </div>
            </div>

            <div className="border rounded-2xl cursor-pointer flex-1/2">
              <div className="flex gap-2 bg-gray-100 rounded-t-2xl p-4">
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
              <div className="flex gap-2 bg-gray-100 rounded-t-2xl p-4">
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

          {/* ✅ زر بدء الاختبار */}
          <div className="flex justify-center mt-4">
            <Button
              variant={"outline"}
              className="p-6 font-bold"
              onClick={() => setStarted(true)} // ✅ هنا التغيير يحصل عند الضغط
            >
              <PencilSquareIcon className="w-7 h-7 font-bold" />
              ابدأ الاختبار
            </Button>
          </div>
        </div>
      )}

      {/* ✅ الجزء الثاني يظهر فقط بعد بدء الاختبار */}
      {started && (
        <div>
          <div className="flex justify-between">
            <div>
            <p className="font-bold">عنوان تحفيزى</p>
            <p className="text-gray-600 float-right">وصف</p>   
             </div> 
            <button className="flex items-center gap-3 border border-[#f34b4b] p-3 font-semibold rounded-lg text-[#f34b4b]"><ArrowRightEndOnRectangleIcon className="w-5 h-5"/>انهاء التدريب</button>
          </div>
           <div className="flex justify-between gap-2 items-center mt-4 mx-40">
              <div className="bg-[#9ec9fa] w-full h-2 rounded-full overflow-hidden mr-4">
                <div className="bg-[#074182] h-full" style={{ width: "33%" }}></div>
              </div>
              <span className="text-sm font-bold text-blue-600">10/30</span>
            </div>
          <div className="two flex flex-col lg:flex-row gap-6 mt-4">
            {/* منطقة السؤال والإجابات */}
            <div>
          <div className="border rounded-2xl flex-1 pb-4">
            <div className="flex justify-between mb-4 flex-wrap gap-3 bg-[#074182] p-5 rounded-t-2xl">
              <p className="text-white font-semibold">نوع السؤال</p>  
              <div className="flex gap-2">
                <button className="border text-white py-2 px-4 rounded-md text-sm">⭐ تمييز</button>
                <span className="bg-gray-100 py-1 px-3 rounded-md text-sm flex items-center">⏱ 05:30</span>
                <button className="bg-yellow-400 text-white py-1 px-3 rounded-md text-sm flex items-center gap-2 font-semibold"><ExclamationTriangleIcon className="w-5 h5"/>ابلاغ عن خطأ</button>
              </div>
              </div>
            <p className="font-bold text-xl leading-8 text-gray-800 p-3 border-b border-gray-200">
              نص السؤال نص السؤال نص السؤال نص السؤال نص السؤال نص السؤال نص السؤال نص السؤال نص السؤال
            </p>
            <div className="grid grid-cols-2 gap-4 mt-5 p-3">
              <button className="border border-[#074182] rounded-lg p-4 text-center bg-[#9ec9fa]">خيار1</button>
              <button className="border border-[#074182] rounded-lg p-4 text-center hover:bg-[#9ec9fa]">خيار2</button>
              <button className="border border-[#074182] rounded-lg p-4 text-center hover:bg-[#9ec9fa]">خيار3</button>
              <button className="border border-[#074182] rounded-lg p-4 text-center hover:bg-[#9ec9fa]">خيار4</button>
            </div>
              </div>
              <div className="flex justify-center gap-3 font-bold mt-5">
              <Button variant={"outline"} className="font-semibold py-6 px-9"><CheckIcon className="w-5 h-5"/>تأكيد الاجابة</Button>
              <Button variant={"default"} className="font-semibold py-6 px-9">التالي ←</Button>
            </div>
              </div>
          {/* لوحة النتائج الجانبية */}
          <div className="border rounded-2xl w-full lg:w-1/4 bg-white">
            <p className="font-bold text-lg mb-3 bg-[#074182] text-white rounded-t-2xl">خيارات متقدمة</p>
            <div className="flex justify-between mb-2">
              <p className="text-red-600">0</p>
              <p className="text-gray-600">إجابة خاطئة</p>
            </div>
            <div className="flex justify-between mb-2">
              <p className="text-green-600">2</p>
              <p className="text-gray-600">إجابة صحيحة</p>
            </div>
            <div className="flex justify-between mb-4">
              <p className="text-yellow-600">10</p>
              <p className="text-gray-600">النقاط الكلية</p>
            </div>
            <div className="border-t pt-3">
              <p className="text-sm font-bold mb-2 text-gray-700">وسائل المساعدة</p>
              <div className="flex flex-col gap-2">
                <button className="border p-2 rounded-md text-red-600">حذف إجابة</button>
                <button className="border p-2 rounded-md text-yellow-600">اعطاء تلميح</button>
                <button className="border p-2 rounded-md text-green-600">عرض طريقة الحل</button>
              </div>
            </div>
          </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TraditionalEdu;
