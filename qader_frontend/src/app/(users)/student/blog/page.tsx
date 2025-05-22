"use client"
// BlogSupportSection.tsx
import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

const blogData = [
  { title: 'عنوان المقال التعليمي', date: 'January 22, 2023', image: '/images/articles.jpg' },
  { title: 'عنوان المقال التعليمي', date: 'January 22, 2023', image: '/images/articles.jpg' },
  { title: 'عنوان المقال التعليمي', date: 'January 22, 2023', image: '/images/articles.jpg' },
  { title: 'عنوان المقال التعليمي', date: 'January 22, 2023', image: '/images/articles.jpg' },
];

const BlogCard = ({ title, date, image }: any) => (
  <div className="rounded-xl overflow-hidden shadow-sm relative group">
    <img src={image} alt={title} className="w-full h-48 object-cover" />
    <div
      className="absolute inset-0 bg-gradient-to-t from-[#074182cc] to-transparent p-4 flex flex-col justify-end text-white"
      style={{
        background:
          'linear-gradient(0deg, rgba(7, 65, 130, 0.8) 0%, rgba(7, 65, 130, 0) 100%)',
      }}
    >
      <h4 className="text-sm font-bold">{title}</h4>
      <p className="text-xs">{date}</p>
    </div>
  </div>
);

const BlogSupportSection = () => {
  const [showEducation, setShowEducation] = useState(true);
  const [showStrategies, setShowStrategies] = useState(true);

  return (
    <section className="container mx-auto p-4 space-y-6 max-w-screen-xl">
      {/* Categories section */}
      <div className="space-y-4">
        {/* Category 1 */}
        <div className="bg-white dark:bg-[#0B1739] p-4 rounded-xl shadow-sm">
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => setShowEducation(!showEducation)}
          >
            <h3 className="font-bold">مقالات تعليمية</h3>
            {showEducation ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </div>
          {showEducation && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mt-4">
              {blogData.slice(0, 6).map((blog, i) => (
                <BlogCard key={i} {...blog} />
              ))}
            </div>
          )}
        </div>

        {/* Category 2 */}
        <div className="bg-white dark:bg-[#0B1739] p-4 rounded-xl shadow-sm">
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => setShowStrategies(!showStrategies)}
          >
            <h3 className="font-bold">استراتيجيات الحل الذكية</h3>
            {showStrategies ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </div>
          {showStrategies && (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mt-4">
              {blogData.slice(0, 6).map((blog, i) => (
                <BlogCard key={i} {...blog} />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Support form section */}
      <div className="bg-white dark:bg-[#0B1739] p-6 rounded-xl shadow-sm flex flex-col lg:flex-row gap-6">
        <form className="flex-1 space-y-4">
          <div>
            <label className="block text-sm font-bold mb-1">نوع المشكلة</label>
            <input
              type="text"
              placeholder="صعوبة في المذاكرة"
              className="w-full border rounded-md p-2"
            />
          </div>
          <div>
            <label className="block text-sm font-bold mb-1">وصف المشكلة</label>
            <textarea
              rows={4}
              placeholder="اكتب وصف المشكلة..."
              className="w-full border rounded-md p-2"
            />
          </div>
          <button className="bg-[#074182] text-white px-4 py-2 rounded-md hover:bg-[#05356a] transition">
            ✉️ إرسال
          </button>
        </form>

        <div className="lg:w-1/2 ">
          <h3 className="text-md font-bold mb-2">هل تواجه مشكلة؟! <span className="text-[#074182]">اطلب نصيحة</span></h3>
          <p className="text-sm text-gray-600">
            - اكتب لنا المشكلة التي تواجه صعوبة فيها. <br />
            - سيتم الرد و <a href="#" className="text-blue-600 underline">الدعم الخارجي</a> يمكنه خدمتك لاحقاً بدون ذكر اسمك.
          </p>
        </div>
      </div>
    </section>
  );
};

export default BlogSupportSection;
