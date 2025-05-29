"use client";

import React from "react";
import Image from "next/image";
import {
  Facebook,
  Twitter,
  Linkedin,
  Mail,
} from "lucide-react";

const ArticlePage = () => {
  return (
    <div className="max-w-3xl mx-auto p-4 space-y-10 text-right">
      {/* Cover Image + Title */}
      <div className="relative w-full h-64 rounded-lg overflow-hidden">
        <Image
          src='/images/articles.jpg'
          alt="cover"
          fill
          className="object-cover"
        />
        <div className="absolute inset-0 bg-black/40 flex flex-col justify-center items-center text-white p-4">
          <h1 className="text-2xl font-bold mb-1">عنوان المقال</h1>
          <p className="text-sm">February 12, 2023 · اسم الكاتب</p>
        </div>
      </div>

      {/* Article Body */}
      <div className="text-justify leading-7 space-y-5">
        {[...Array(5)].map((_, i) => (
          <p key={i}>
            نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال نص المقال
          </p>
        ))}
      </div>

      {/* Author Card */}
      <div className="bg-gray-100 dark:bg-[#1f2937] text-center p-6 rounded-xl">
        <div className="flex justify-center">
          <Image
            src="/images/avatar.png"
            alt="الكاتب"
            width={60}
            height={60}
            className="rounded-full"
          />
        </div>
        <p className="font-bold mt-2">اسم الكاتب</p>
        <p className="text-sm text-gray-600 dark:text-gray-300">وصف عن صاحب المقال</p>
        <div className="flex justify-center gap-4 mt-4 text-gray-700 dark:text-white">
          <a href="#" aria-label="Facebook"><Facebook size={18} /></a>
          <a href="#" aria-label="Email"><Mail size={18} /></a>
          <a href="#" aria-label="Twitter"><Twitter size={18} /></a>
          <a href="#" aria-label="LinkedIn"><Linkedin size={18} /></a>
        </div>
      </div>
    </div>
  );
};

export default ArticlePage;
