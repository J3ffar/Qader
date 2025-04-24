"use client";

import React, { useRef, useState } from "react";
import Image from "next/image";
import {
  PencilIcon,
  ChevronDownIcon,
  UserIcon,
} from "@heroicons/react/24/solid";
import { Button } from "@/components/ui/button";
import Link from "next/link";

const Completsignup = () => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectOpen, setSelectOpen] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleDivClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      console.log("الصورة المختارة:", file);
    }
  };

  const handleSubmit = () => {
    setShowSuccess(true);
    setTimeout(() => {
      setShowSuccess(false);
    }, 3000);
  };

  return (
    <div className="w-full max-w-[500px] mx-auto p-6 space-y-4 relative">
      {/* popup success */}
      {showSuccess && (
        <div className="fixed inset-0 bg-black/40 bg-opacity-30 flex justify-center items-center h-full z-50">
          <div className="bg-white p-6 rounded-2xl shadow-lg flex justify-center items-center flex-col">
            <Image src={"/images/success.gif"} width={100} height={100} alt="" />
            <p className="text-xl font-bold mt-2">تم التسجيل بنجاح</p>
            <p className="text-gray-500 mt-3">سيتم الانتقال مباشرةً إلى صفحتك</p>
          </div>
        </div>
      )}

      <div className="text-center">
        <h2 className="text-4xl font-bold">أكمل التسجيل</h2>
        <p className="text-gray-500 text-xl">نص نص نص نص نص نص</p>
      </div>

      <div className="flex flex-col items-center gap-2">
        <input
          type="file"
          accept="image/*"
          ref={fileInputRef}
          className="hidden"
          onChange={handleFileChange}
        />
        <div
          className="relative w-[100px] h-[100px] cursor-pointer"
          onClick={handleDivClick}
        >
          <Image
            src="/images/signup.png"
            width={100}
            height={100}
            alt=""
            className="rounded-full object-cover w-full h-full"
          />
          <PencilIcon className="w-5 h-5 text-[#2f80ed] bg-white p-1 rounded-full absolute bottom-0 right-0 shadow-md" />
        </div>
      </div>

      <form className="space-y-4 text-right" onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
        {/* الجنس */}
        <div className="relative">
          <label className="block mb-1 font-bold">الجنس</label>
          <select
            className="w-full border rounded-md p-2 appearance-none"
            onFocus={() => setSelectOpen(true)}
            onBlur={() => setSelectOpen(false)}
          >
            <option>ذكر</option>
            <option>أنثى</option>
          </select>
          <ChevronDownIcon
            className={`w-5 h-5 absolute left-3 top-[50px] transform -translate-y-1/2 transition-transform duration-300 ease-in-out ${
              selectOpen ? "rotate-180 text-gray-500" : "text-gray-500"
            }`}
          />
        </div>

        {/* الاسم */}
        <div className="relative">
          <label className="block mb-1 font-bold">الاسم الذي تحب أن اناديك به</label>
          <input
            type="text"
            className="w-full border rounded-md p-2 pr-10"
            placeholder="سالم"
          />
          <UserIcon className="w-5 h-5 absolute right-3 top-[47px] transform -translate-y-1/2 text-gray-400" />
        </div>

        {/* الصف */}
        <div className="relative">
          <label className="block mb-1 font-bold">الصف</label>
          <select
            className="w-full border rounded-md p-2 appearance-none"
            onFocus={() => setSelectOpen(true)}
            onBlur={() => setSelectOpen(false)}
          >
            <option>ثاني ثانوي</option>
            <option>ثالث ثانوي</option>
          </select>
          <ChevronDownIcon
            className={`w-5 h-5 absolute left-3 top-[50px] transform -translate-y-1/2 transition-transform duration-300 ease-in-out ${
              selectOpen ? "rotate-180 text-gray-500" : "text-gray-500"
            }`}
          />
        </div>

        {/* قدرات */}
        <div>
          <label className="block mb-1 font-bold">هل اختبرت قدرات من قبل؟</label>
          <div className="flex gap-4">
            <button type="button" className="border rounded-md px-4 py-2 w-full cursor-pointer hover:bg-gray-100">
              نعم
            </button>
            <button type="button" className="border rounded-md px-4 py-2 w-full cursor-pointer hover:bg-gray-100">
              لا
            </button>
          </div>
        </div>

        {/* الشرف */}
        <div>
          <label className="block mb-1">المعرف</label>
          <input
            type="text"
            className="w-full border rounded-md p-2"
            placeholder="سالم"
          />
        </div>

        {/* الرمز التسلسلي */}
        <div>
          <label className="block mb-1">الرمز التسلسلي</label>
          <input
            type="text"
            className="w-full border rounded-md p-2"
            placeholder="سالم"
          />
        </div>

        {/* شروط وأحكام */}
        <p className="text-xs text-gray-600">
          في حال لم يكن لديك، فيمكنك طلب واحد من{" "}
          <Link href="/" className="text-blue-600 underline">هذه الصفحة</Link>
        </p>

        <div className="flex items-center gap-2">
          <input type="checkbox" />
          <label className="text-sm">
            أنت توافق على{" "}
            <Link href="/conditions" className="text-blue-600 underline">الشروط والأحكام</Link>{" "}
            تلقائيًا في حال التسجيل.
          </label>
        </div>

        {/* زر الاشتراك */}
        <Button variant={"outline"} className="w-full" type="submit">
          تسجيل الاشتراك
              </Button>
              <Link href={"/"}>
                <Button variant={"default"} className="w-full">
                  السابق
                </Button>
                </Link>
      </form>
    </div>
  );
};

export default Completsignup;
