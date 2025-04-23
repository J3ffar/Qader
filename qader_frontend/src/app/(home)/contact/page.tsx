'use client'

import React, { useState } from 'react';
import { FolderOpenIcon, PaperAirplaneIcon,UserIcon } from '@heroicons/react/24/outline';
import { Button } from "@/components/ui/button";
import Image from "next/image";



const ContactUs = () => {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [file, setFile] = useState<File | null>(null);

  // للتحكم في عرض الهنت عند الفوكس
  const [isUsernameFocused, setIsUsernameFocused] = useState(false);
  const [isEmailFocused, setIsEmailFocused] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  return (
    <div className='flex justify-center items-center p-8 gap-6 max-md:flex-col' >
      <div className='flex flex-col gap-5 flex-1/2 p-9'>
        <Image src={"/images/group.png"} width={500} height={500} alt='' />
        <h2 className='text-4xl font-bold max-md:text-center'>لنبق على اتصال, <span className='text-[#074182]'>نحن هنا لمساعتك!</span></h2>
        <p>إذا كنت تودالإتصال من أجل مشكلة أوإستفسار حول متجرك, ينصح استعمال منطقه الدعم الموجوده داخل لوحة التحكم بحسابك من أجل دعم سريع وسرية اكبر. أو يمكنط الإستفسار حول أمور عامة عن طريق ارسال رسالة من هنا</p>
        <h3 className='font-bold text-2xl'>او تواصل معنا</h3>
        <div className='flex gap-3'>
          <Image src={"/images/gmail.png"} width={10} height={10} className='w-10 h-10 p-2 rounded-full bg-gray-200 transition delay-150 duration-300 ease-in-out hover:bg-gray-300' alt='' />
          <Image src={"/images/send-2.png"} width={40} height={40} className='w-10 h-10 p-2 rounded-full bg-gray-200 transition delay-150 duration-300 ease-in-out hover:bg-gray-300' alt='' /> 
        </div>
      </div>
      <div className="max-w-lg mx-auto p-6 bg-white shadow-xl rounded-lg flex-1/2">
      <div className="space-y-4">
        {/* Full Name */}
       <div className="space-y-2">
  <label htmlFor="username" className="block text-gray-700 font-bold">الاسم بالكامل</label>

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
      className="w-full pl-4 pr-10 py-2 bg-gray-100 rounded-md focus:outline-none focus:border focus:border-[#F34B4B] focus:placeholder:text-[#F34B4B]"
    />
  </div>

  {isUsernameFocused && (
    <p className="text-[#F34B4B] text-xs">يجب أن يحتوي على حروف إنجليزية وأرقام فقط.</p>
  )}
</div>

        {/* Email */}
 <div className="space-y-2">
  <label htmlFor="email" className="block text-gray-700 font-bold">البريد الإلكتروني</label>

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
      className="w-full pl-4 pr-10 py-2 bg-gray-100 rounded-md focus:outline-none focus:border focus:border-[#F34B4B] focus:placeholder:text-[#F34B4B]"
    />
  </div>

  {isEmailFocused && (
    <p className="text-[#F34B4B] text-xs">*الرجاء التأكد من صحة الأيميل</p>
  )}
</div>

        {/* Subject */}
        <div className="space-y-2">
          <label htmlFor="subject" className="block text-gray-700 font-bold">عنوان الموضوع</label>
          <input 
            id="subject" 
            type="text" 
            placeholder="ادخل عنوان الموضوع" 
            value={subject} 
            onChange={(e) => setSubject(e.target.value)} 
            className="w-full px-4 py-2 bg-gray-100 rounded-md focus:outline-none focus:border"
          />
        </div>

        {/* Message */}
        <div className="space-y-2">
          <label htmlFor="message" className="block text-gray-700 font-bold">الرسالة</label>
          <textarea 
            id="message" 
            placeholder="اكتب رسالتك هنا" 
            value={message} 
            onChange={(e) => setMessage(e.target.value)} 
            className="w-full px-4 py-2 bg-gray-100 rounded-md focus:outline-none focus:border"
          />
        </div>

        {/* File Upload */}
        <div className="space-y-2">
  <label htmlFor="file" className="block text-gray-700 font-bold">ارفاق ملف</label>
  
  <label
    htmlFor="file"
    className="flex items-center justify-center gap-2 w-full h-32 px-4 py-6 border-2 border-dashed border-gray-300 rounded-md cursor-pointer hover:border-blue-400 bg-gray-100 transition"
  >
    <FolderOpenIcon className="h-6 w-6 text-gray-500" />
    <span className="text-gray-600">ارفاق ملف</span>
  </label>

  <input
    id="file"
    type="file"
    onChange={handleFileChange}
    className="hidden"
  />
</div>


        <div className="flex justify-center">
          <Button variant="outline" className="w-full flex items-center justify-center gap-2">
            إرسال
              <PaperAirplaneIcon className="h-5 w-5 text-white" />
          </Button>
      </div>

      </div>
      </div>
    </div>
  );
};

export default ContactUs;
