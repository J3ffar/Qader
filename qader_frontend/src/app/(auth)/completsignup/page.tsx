"use client";

import React, { useEffect, useRef, useState } from "react";
import Image from "next/image";
import {
  PencilIcon,
  ChevronDownIcon,
  UserIcon,
} from "@heroicons/react/24/solid";
import { useRouter } from "next/navigation";
import Link from "next/link";

const Completsignup = () => {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectOpen, setSelectOpen] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const [form, setForm] = useState({
    gender: "",
    preferred_name: "",
    grade: "",
    has_taken_qiyas_before: false,
    username: "",
    serial_code: "",
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      console.log("الصورة المختارة:", file);
    }
  };

  const handleSubmit = async () => {
    try {
      const step1 = JSON.parse(localStorage.getItem("signup-step1") || "{}");

      const payload = {
        full_name: step1.full_name,
        email: step1.email,
        password: step1.password,
        password_confirm: step1.password,
        gender: form.gender === "أنثى" ? "female" : "male",
        preferred_name: form.preferred_name,
        grade: form.grade,
        has_taken_qiyas_before: form.has_taken_qiyas_before,
        username: form.username,
        serial_code: form.serial_code,
      };

      const res = await fetch("https://qader.vip/ar/api/v1/auth/register/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        alert("فشل التسجيل: " + JSON.stringify(data));
        return;
      }

      setShowSuccess(true);
      localStorage.removeItem("signup-step1");

      setTimeout(() => {
        router.push("/dashboard"); // or redirect to login
      }, 3000);
    } catch (err) {
      alert("فشل الاتصال بالخادم");
    }
  };

  return (
    <div className="w-full max-w-[500px] mx-auto p-6 space-y-4 relative">
      {/* Success Popup */}
      {showSuccess && (
        <div className="fixed inset-0 bg-black/40 flex justify-center items-center z-50">
          <div className="bg-white p-6 rounded-2xl shadow-lg flex flex-col items-center">
            <Image src={"/images/success.gif"} width={100} height={100} alt="نجاح" />
            <p className="text-xl font-bold mt-2">تم التسجيل بنجاح</p>
            <p className="text-gray-500 mt-3">سيتم الانتقال مباشرةً إلى صفحتك</p>
          </div>
        </div>
      )}

      <div className="text-center">
        <h2 className="text-4xl font-bold">أكمل التسجيل</h2>
        <p className="text-gray-500 text-xl">الرجاء إدخال التفاصيل المتبقية</p>
      </div>

      {/* صورة الملف */}
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
          onClick={() => fileInputRef.current?.click()}
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

      <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }} className="space-y-4 text-right">
        {/* Gender */}
        <div className="relative">
          <label className="block mb-1 font-bold">الجنس</label>
          <select
            className="w-full border rounded-md p-2 appearance-none dark:bg-[#0B1739] dark:text-[#FDFDFD]"
            value={form.gender}
            onChange={(e) => setForm({ ...form, gender: e.target.value })}
            onFocus={() => setSelectOpen(true)}
            onBlur={() => setSelectOpen(false)}
          >
            <option value="">اختر الجنس</option>
            <option>ذكر</option>
            <option>أنثى</option>
          </select>
          <ChevronDownIcon
            className={`w-5 h-5 absolute left-3 top-[50px] transform -translate-y-1/2 transition-transform duration-300 ease-in-out ${selectOpen ? "rotate-180" : ""}`}
          />
        </div>

        {/* Preferred Name */}
        <div >
          <label className="block mb-1 font-bold">الاسم المفضل</label>
          <div className="relative">
          <input
            type="text"
            className="w-full border rounded-md p-2 pr-10"
            placeholder="سالم"
            value={form.preferred_name}
            onChange={(e) => setForm({ ...form, preferred_name: e.target.value })}
          />
          <UserIcon className="w-5 h-5 absolute right-3 top-[50%] translate-y-[-50%] text-gray-400" />
          </div>
        </div>

        {/* Grade */}
        <div className="relative">
          <label className="block mb-1 font-bold">الصف</label>
          <select
            className="w-full border rounded-md p-2 appearance-none dark:bg-[#0B1739] dark:text-[#FDFDFD]"
            value={form.grade}
            onChange={(e) => setForm({ ...form, grade: e.target.value })}
          >
            <option value="">اختر الصف</option>
            <option>أولى ثانوي</option>
            <option>ثاني ثانوي</option>
            <option>ثالث ثانوي</option>
          </select>
        </div>

        {/* Qudurat Test */}
        <div>
        <div>
  <label className="block mb-1 font-bold">هل اختبرت قدرات من قبل؟</label>
  <div className="flex gap-4">
    <button
      type="button"
      className={`border rounded-md px-4 py-2 w-full transition
        ${form.has_taken_qiyas_before
          ? "bg-blue-100 dark:bg-blue-900 font-bold"
          : "bg-white dark:bg-[#0B1739] font-normal"
        }`}
      onClick={() => setForm({ ...form, has_taken_qiyas_before: true })}
    >
      نعم
    </button>
    <button
      type="button"
      className={`border rounded-md px-4 py-2 w-full transition
        ${!form.has_taken_qiyas_before
          ? "bg-blue-100 dark:bg-blue-900 font-bold"
          : "bg-white dark:bg-[#0B1739] font-normal"
        }`}
      onClick={() => setForm({ ...form, has_taken_qiyas_before: false })}
    >
      لا
    </button>
  </div>
</div>

        </div>

        {/* Username */}
        <div>
          <label className="block mb-1 font-bold">اسم المستخدم</label>
          <input
            type="text"
            className="w-full border rounded-md p-2"
            placeholder="username123"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
          />
        </div>

        {/* Serial Code */}
        <div>
          <label className="block mb-1 font-bold">الرمز التسلسلي</label>
          <input
            type="text"
            className="w-full border rounded-md p-2"
            placeholder="QADER-ABC123"
            value={form.serial_code}
            onChange={(e) => setForm({ ...form, serial_code: e.target.value })}
          />
        </div>

        {/* Terms and Submit */}
        <p className="text-xs text-gray-600">
          في حال لم يكن لديك رمز، يمكنك طلب واحد من{" "}
          <Link href="/" className="text-[#074182] underline">هذه الصفحة</Link>
        </p>

        <div className="flex items-center gap-2">
          <input type="checkbox" required />
          <label className="text-sm">
            أوافق على{" "}
            <Link href="/conditions" className="text-[#074182] underline">
              الشروط والأحكام
            </Link>
          </label>
        </div>

        <div className="flex flex-col justify-center items-center gap-3 mt-6">
          <button
            type="submit"
            className="w-full sm:w-[380px] p-2 rounded-[8px] bg-[#074182] text-white font-bold hover:bg-[#063462] transition"
          >
            تسجيل الاشتراك
          </button>
          <Link href="/">
            <button className="w-full sm:w-[380px] p-2 rounded-[8px] border border-[#074182] text-[#074182] font-bold hover:bg-[#07418211] transition">
              السابق
            </button>
          </Link>
        </div>
      </form>
    </div>
  );
};

export default Completsignup;
