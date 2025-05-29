"use client";

import React, { useState } from "react";
import {
  FolderOpenIcon,
  PaperAirplaneIcon,
  UserIcon,
} from "@heroicons/react/24/outline";
import { Button } from "@/components/ui/button";
import Image from "next/image";

const ContactUs = () => {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const [isUsernameFocused, setIsUsernameFocused] = useState(false);
  const [isEmailFocused, setIsEmailFocused] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async () => {
    const formData = new FormData();
    formData.append("full_name", username);
    formData.append("email", email);
    formData.append("subject", subject);
    formData.append("message", message);

    if (file) {
      formData.append("attachment", file); // Replace "attachment" if the backend expects a different key
    }

    try {
      const res = await fetch("https://qader.vip/ar/api/v1/content/contact-us/", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      console.log("✅ Contact form submitted:", data);

      if (!res.ok) {
        alert("❌ فشل في إرسال الرسالة: " + JSON.stringify(data));
        return;
      }

      alert("✅ تم إرسال رسالتك بنجاح!");
      setUsername("");
      setEmail("");
      setSubject("");
      setMessage("");
      setFile(null);
    } catch (error) {
      console.error("❌ Error submitting contact form:", error);
      alert("حدث خطأ أثناء إرسال الرسالة");
    }
  };

  return (
    <div className="bg-white dark:bg-[#081028] sm:px-0 px-3">
      <div className="flex justify-center items-center p-8 gap-6 max-md:flex-col">
        <div className="flex flex-col gap-5 flex-1/2 p-9">
          <Image src={"/images/group.png"} width={500} height={500} alt="" />
          <h2 className="text-4xl font-bold max-md:text-center">
            لنبق على اتصال,{" "}
            <span className="text-[#074182]">نحن هنا لمساعدتك!</span>
          </h2>
          <p className="max-w-xl">
            إذا كنت تود الاتصال من أجل مشكلة أو استفسار حول متجرك، يُنصح
            باستعمال منطقة الدعم داخل لوحة التحكم للحصول على دعم سريع وسري. أو
            يمكنك الاستفسار عن أمور عامة من خلال إرسال رسالة من هنا.
          </p>
          <h3 className="font-bold text-2xl">أو تواصل معنا</h3>
          <div className="flex gap-3">
            <Image
              src={"/images/gmail.png"}
              width={10}
              height={10}
              className="w-10 h-10 p-2 rounded-full bg-gray-200 hover:bg-gray-300 transition"
              alt=""
            />
            <Image
              src={"/images/send-2.png"}
              width={40}
              height={40}
              className="w-10 h-10 p-2 rounded-full bg-gray-200 hover:bg-gray-300 transition"
              alt=""
            />
          </div>
        </div>

        <div className="max-w-lg mx-auto p-6 bg-white dark:bg-[#0B1739] shadow-xl rounded-lg flex-1/2">
          <div className="space-y-4">
            {/* Full Name */}
            <div className="space-y-2">
              <label
                htmlFor="username"
                className="block text-[#0C1019] font-bold dark:text-[#FDFDFD]"
              >
                الاسم بالكامل
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                  <UserIcon className="h-5 w-5 text-gray-400" />
                </span>
                <input
                  id="username"
                  type="text"
                  placeholder="ادخل اسم المستخدم"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  onFocus={() => setIsUsernameFocused(true)}
                  onBlur={() => setIsUsernameFocused(false)}
                  className="w-full pl-4 pr-10 py-2 bg-gray-100 dark:bg-transparent rounded-md focus:outline-none focus:border focus:border-[#F34B4B] focus:placeholder:text-[#F34B4B]"
                />
              </div>
              {isUsernameFocused && (
                <p className="text-[#F34B4B] text-xs">
                  يجب أن يحتوي على حروف إنجليزية وأرقام فقط.
                </p>
              )}
            </div>

            {/* Email */}
            <div className="space-y-2">
              <label
                htmlFor="email"
                className="block text-[#0C1019] font-bold dark:text-[#FDFDFD]"
              >
                البريد الإلكتروني
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                  <UserIcon className="h-5 w-5 text-gray-400" />
                </span>
                <input
                  id="email"
                  type="email"
                  placeholder="ادخل بريدك الإلكتروني"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onFocus={() => setIsEmailFocused(true)}
                  onBlur={() => setIsEmailFocused(false)}
                  className="w-full pl-4 pr-10 py-2 bg-gray-100 dark:bg-transparent rounded-md focus:outline-none focus:border focus:border-[#F34B4B] focus:placeholder:text-[#F34B4B]"
                />
              </div>
              {isEmailFocused && (
                <p className="text-[#F34B4B] text-xs">
                  *الرجاء التأكد من صحة البريد الإلكتروني
                </p>
              )}
            </div>

            {/* Subject */}
            <div className="space-y-2">
              <label
                htmlFor="subject"
                className="block text-[#0C1019] font-bold dark:text-[#FDFDFD]"
              >
                عنوان الموضوع
              </label>
              <input
                id="subject"
                type="text"
                placeholder="ادخل عنوان الموضوع"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                className="w-full px-4 py-2 bg-gray-100 dark:bg-transparent rounded-md focus:outline-none focus:border"
              />
            </div>

            {/* Message */}
            <div className="space-y-2">
              <label
                htmlFor="message"
                className="block text-[#0C1019] font-bold dark:text-[#FDFDFD]"
              >
                الرسالة
              </label>
              <textarea
                id="message"
                placeholder="اكتب رسالتك هنا"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full px-4 py-2 bg-gray-100 dark:bg-transparent rounded-md focus:outline-none focus:border"
              />
            </div>

            {/* File Upload */}
            <div className="space-y-2">
              <label
                htmlFor="file"
                className="block text-[#0C1019]  font-bold dark:text-[#FDFDFD]"
              >
                إرفاق ملف
              </label>
              <label
                htmlFor="file"
                className="flex items-center justify-center gap-2 w-full h-32 px-4 py-6 border-2 border-dashed border-gray-300 rounded-md cursor-pointer hover:border-blue-400 bg-gray-100 dark:bg-transparent transition"
              >
                <FolderOpenIcon className="h-6 w-6 text-gray-500" />
                <span className="text-gray-600">
                  {file ? file.name : "إرفاق ملف"}
                </span>
              </label>
              <input
                id="file"
                type="file"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>

            {/* Submit Button */}
            <div className="flex justify-center">
              <Button
                variant="outline"
                className="w-full flex items-center justify-center gap-2"
                onClick={handleSubmit}
              >
                إرسال
                <PaperAirplaneIcon className="h-5 w-5 text-white" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContactUs;
