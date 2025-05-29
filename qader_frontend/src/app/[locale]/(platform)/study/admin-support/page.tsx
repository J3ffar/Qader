"use client";

import React, { useState } from "react";
import { ChevronDownIcon } from "@heroicons/react/24/solid";
import { Button } from "@/components/ui/button";
import { Search, UploadCloud } from "lucide-react";

const faqs = [
  {
    question: "كيف يتم الاشتراك في المنصة؟",
    answer: "شرح طريقة الاشتراك في وجود خطوات بسيطة للتنقل.",
  },
  { 
    question: "السؤال", 
    answer: "الإجابة" 
  },
  { 
    question: "السؤال", 
    answer: "الإجابة" 
  },
  { 
    question: "السؤال", 
    answer: "الإجابة" 
   },
];

const tickets = [
  { id: 1, date: "23/2/25", status: "قيد المراجعة" },
  { id: 2, date: "23/2/25", status: "مغلق" },
  { id: 3, date: "23/2/25", status: "مغلق" },
  { id: 4, date: "23/2/25", status: "جديد" },
];

const SupportCenter = () => {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);
  const [form, setForm] = useState({
    type: "",
    description: "",
    file: null as File | null,
  });

  const toggleFAQ = (index: number) => {
    setExpandedIndex(index === expandedIndex ? null : index);
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "جديد":
        return "bg-blue-100 text-blue-600";
      case "قيد المراجعة":
        return "bg-yellow-100 text-yellow-600";
      case "مغلق":
        return "bg-red-100 text-red-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  return (
    <div className="p-6 text-right space-y-6 max-w-6xl mx-auto font-sans">
      <div>
        <h2 className="text-lg font-bold text-gray-700">الدعم الإداري</h2>
      <p className="text-sm text-gray-500">
        شاركنا استفساراتك لنساعدك أكثر
      </p>
      </div>

      <div>
        <h2 className="text-xl mt-4 font-bold text-gray-700">الاسئلة الشائعة</h2>
      <p className="text-sm text-gray-500">
لديك سؤال؟ لدينا الاجابة، ابحث عن سؤالك هنا.      </p>
      <p className="text-sm text-gray-500">
لديك سؤال؟ لدينا الاجابة، ابحث عن سؤالك هنا لديك سؤال؟ لدينا الاجابة، ابحث عن سؤالك هنا 
      </p>
      </div>

      <div className=" flex justify-between h-[56px]  max-w-[520px] mx-auto">
        <input
          type="text"
          placeholder="ابحث عن سؤالك هنا..."
          className="w-full border p-2 rounded-md text-sm h-full"
        />
        <button className=" h-[56px] w-[72px] rounded-[16px] mr-2 bg-[#074182] flex justify-center items-center">
            <Search className=" text-white"/>
        </button>
      </div>


      {/* FAQ Search */}
      <div className="border rounded-lg p-4 shadow-sm max-w-4xl mx-auto ">
        

        <div className="mt-4 divide-y">
          {faqs.map((item, index) => (
            <div key={index}>
              <button
                onClick={() => toggleFAQ(index)}
                className="w-full flex justify-between items-center py-3 text-right text-sm font-semibold text-gray-700"
              >
                {item.question}
                <ChevronDownIcon
                  className={`w-5 h-5 transform transition-transform ${
                    expandedIndex === index ? "rotate-180" : ""
                  }`}
                />
              </button>
              {expandedIndex === index && (
                <div className="text-sm text-gray-600 pb-3 px-2">{item.answer}</div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
       

        {/* Form */}
        <div className="col-span-1 md:col-span-2 border p-4 rounded-lg shadow-sm">
          <h3 className="font-bold text-sm text-gray-700 mb-4">
            ابدأ محادثة مع الإدارة
          </h3>
          <ul className="text-xs text-gray-500 mb-4 list-disc pr-4">
            <li>أدخل نوع المشكلة</li>
            <li>أدخل وصف واضح للمشكلة</li>
            <li>أرفق مستندًا</li>
          </ul>

          <div className="space-y-3">
            <select
              value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value })}
              className="w-full border p-2 rounded-md text-sm"
            >
              <option value="">نوع المشكلة</option>
              <option value="technical">مشكلة تقنية</option>
              <option value="billing">مشكلة في الفواتير</option>
            </select>
            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full border p-2 rounded-md text-sm"
              rows={4}
              placeholder="اكتب وصف المشكلة..."
            ></textarea>
            <label className="block text-sm font-medium text-gray-600">
              (ارفاق مستند اختياري)
            </label>
            <div className="border-2 border-dashed p-4 text-center text-sm rounded-md cursor-pointer">
              <input
                type="file"
                className="hidden"
                onChange={(e) =>
                  setForm({ ...form, file: e.target.files?.[0] || null })
                }
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer block">
                <UploadCloud className="mx-auto w-6 h-6 mb-2 text-gray-500" />
                {form.file ? form.file.name : "ارفع صورة هنا"}
              </label>
            </div>
            <Button className="w-full bg-[#074182] text-white mt-2 hover:bg-[#053866]">
              إرسال
            </Button>
          </div>
        </div>

         {/* Ticket Table */}
        <div className="col-span-1 border p-4 rounded-lg shadow-sm">
          <h3 className="font-bold mb-4 text-sm text-gray-700">
            سجل حالات الدعم الإداري
          </h3>
          <table className="w-full text-sm">
            <thead className="text-right text-gray-500">
              <tr>
                <th className="py-2">التاريخ</th>
                <th className="py-2">حالة الطلب</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map((ticket) => (
                <tr key={ticket.id} className="border-t">
                  <td className="py-2">{ticket.date}</td>
                  <td className="py-2">
                    <span
                      className={`px-2 py-1 text-xs rounded ${statusColor(
                        ticket.status
                      )}`}
                    >
                      {ticket.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SupportCenter;
