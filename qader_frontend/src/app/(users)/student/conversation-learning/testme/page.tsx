"use client";

import React, { useState } from "react";
import { PaperAirplaneIcon, MicrophoneIcon, PencilIcon, CheckIcon, XMarkIcon } from "@heroicons/react/24/solid";
import Image from "next/image";

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState([
    {
      type: "question",
      text: "نص السؤال",
      options: ["استيعاب المقروء", "استيعاب المقروء", "استيعاب المقروء"],
      selected: "استيعاب المقروء",
    },
    {
      type: "answer",
      status: "correct",
      text: "أحسنت! إجابة صحيحة.",
      explanation: "شرح الإجابة: الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح."
    },
    {
      type: "question",
      text: "نص السؤال",
      options: ["استيعاب المقروء", "استيعاب المقروء", "استيعاب المقروء"],
      selected: null,
    },
    {
      type: "answer",
      status: "wrong",
      text: "إجابة خاطئة",
      explanation: "شرح الإجابة: الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح الشرح."
    }
  ]);

  return (
    <div className="flex flex-col gap-6 bg-white dark:bg-[#081028] p-6 rounded-lg max-w-7xl mx-auto">
      <div className="text-right">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-200">تحدث عبر المحادثة</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">اختر قدراتك مع قادر او اطرح عليه سؤال.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Sidebar */}
        <div className="flex flex-col gap-4 col-span-1">
          <div className="bg-[#F5F7FA] dark:bg-[#081028] border p-4 rounded-xl text-center">
            <div className="w-full h-24 bg-gray-200 rounded-lg mb-3 flex items-center justify-center">
              <Image src="/images/image-line.png" alt="placeholder" width={80} height={80} />
            </div>
            <h3 className="font-bold">اطرح سؤالك</h3>
            <p className="text-sm text-gray-500">اطرح اسئلتك من هنا</p>
            <button className="bg-[#074182] hover:bg-[#053866] text-white mt-3 px-4 py-2 rounded-md text-sm w-full">ابدأ</button>
          </div>
          <div className="bg-[#F5F7FA] dark:bg-[#081028] border p-4 rounded-xl text-center">
            <div className="w-full h-24 bg-gray-200 rounded-lg mb-3 flex items-center justify-center">
              <Image src="/images/image-line.png" alt="placeholder" width={80} height={80} />
            </div>
            <h3 className="font-bold">اختبر قدراتك</h3>
            <p className="text-sm text-gray-500">اختبر قدراتك من هنا</p>
            <button className="bg-[#074182] hover:bg-[#053866] text-white mt-3 px-4 py-2 rounded-md text-sm w-full">اختبرني</button>
          </div>
        </div>

        {/* Chat */}
        <div className="col-span-2 flex flex-col justify-between rounded-xl border dark:bg-[#0B1739] border-gray-200 p-4 min-h-[600px]">
          <div className="flex-1 space-y-6">
            {messages.map((msg : any, i) => (
              <div key={i}>
                {msg.type === "question" && (
                  <div className="bg-white dark:bg-[#081028] border rounded-xl p-4 shadow-sm text-right">
                    <p className="font-bold text-sm mb-3">{msg.text}</p>
                    <div className="flex flex-wrap gap-2">
                      {msg.options.map((opt : any, j : any) => (
                        <button
                          key={j}
                          className={`border px-3 py-1 rounded-md text-sm ${msg.selected === opt ? 'bg-[#074182] text-white' : 'bg-white text-gray-700'}`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {msg.type === "answer" && (
                  <div className={`p-4 rounded-xl ${msg.status === 'correct' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'} text-sm text-right font-bold`}>
                    {msg.text}
                    {msg.explanation && (
                  <div className=" mt-2">
                    <p className="text-sm font-bold mb-1">شرح الإجابة:</p>
                    <p className="text-sm text-gray-700 leading-6">{msg.explanation}</p>
                  </div>
                )}
                    </div>
                )}
                
                {msg.status === 'correct' && (
                  <div className="flex gap-3 mt-2 text-sm justify-end">
                    <button className="px-4 py-1 border rounded-md text-[#074182] border-[#074182]">أعد الشرح</button>
                    <button className="px-4 py-1 bg-[#074182] text-white rounded-md flex gap-1 items-center"><CheckIcon className="w-4 h-4" /> فهمت</button>
                  </div>
                )}
                {msg.status === 'wrong' && (
                  <div className="flex gap-3 mt-2 text-sm justify-end">
                    <button className="px-4 py-1 border rounded-md text-[#074182] border-[#074182]">علمني مرة أخرى</button>
                    <button className="px-4 py-1 bg-[#074182] text-white rounded-md">اخبرني</button>
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="border-t pt-4 mt-4 flex items-center gap-2">
            <input
              type="text"
              placeholder="اكتب سؤالك هنا..."
              className="flex-1 border rounded-md px-4 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button className="bg-[#074182] hover:bg-[#053866] text-white px-4 py-2 rounded-md flex items-center gap-1">
              إرسال
              <PaperAirplaneIcon className="w-4 h-4" />
            </button>
            <button className="bg-gray-100 hover:bg-gray-200 p-2 rounded-md">
              <MicrophoneIcon className="w-5 h-5 text-gray-600" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
