"use client"

import React, { useState } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';
import Image from 'next/image';
import { Button } from '@/components/ui/button';

const Partners: React.FC = () => {
  const [showPopup, setShowPopup] = useState(false);

  return (
    <div className='p-8'>
      <div className='text-center'>
        <h2 className='text-4xl font-bold'>شركاء النجاح</h2>
        <p className='text-gray-800 text-lg mt-4'>لديك سؤال؟ لديناالاجابة, ابحث عن سؤالك هنا...</p>
      </div>

      <div className='flex justify-center items-center gap-4 mt-10 max-md:flex-wrap max-sm:flex-col'>
        {[1, 2, 3].map((_, i) => (
          <div key={i} className='flex flex-col gap-4 justify-center items-center p-4 bg-[#f7fafe] rounded-3xl border border-[#074182] hover:border-[#56769b] hover:scale-105 transition delay-150 duration-300 ease-in-out'>
            <Image src={`/images/partner${i + 1}.png`} width={70} height={70} alt='' />
            <h3 className='text-2xl font-bold'>{`شراكة ${['الطلاب', 'المدارس', 'الدورات'][i]}`}</h3>
            <p className='text-center'>النص هنا النص هنا النص هنا النص هنا النص هنا النص هنا</p>
            <Button variant='outline' onClick={() => setShowPopup(true)}>
              قدم طلب شراكة <PaperAirplaneIcon className='w-5 h-5' />
            </Button>
          </div>
        ))}
      </div>

      <div className='flex justify-center items-center gap-7 mt-14 max-md:flex-col-reverse'>
        <div className='flex-1/2'>
          <h3 className='text-3xl font-bold text-[#074182]'>لماذا الشراكه معنا؟</h3>
          <p>النص هنا النص هنا النص هنا النص هنا النص هنا النص هنا النص هنا النص هنا...</p>
        </div>
        <div className='flex-1/2 flex justify-center'>
          <Image src={'/images/logo.png'} width={400} height={400} alt='' />
        </div>
      </div>

      {/* Popup Modal */}
      {showPopup && (
  <div className='fixed inset-0 bg-black/25 flex justify-center items-center z-50'>
    <div className='bg-white p-10 mx-4 max-lg:mx-6 max-lg:p-6 rounded-xl shadow-lg max-w-4xl w-full max-lg:max-h-[90vh] overflow-y-auto'>
      <div className='flex flex-col justify-center items-center gap-4'>
        <h2 className='text-3xl font-bold'>هل تريد تقديم طلب شراكة؟</h2>
        <div className='flex gap-6 max-md:flex-col'>
          {[
            { label: 'شراكة الطلاب', img: '/images/component 2-1.png' },
            { label: 'شراكة المدارس', img: '/images/Building.png' },
            { label: 'شراكة التدريب', img: '/images/component 2.png' },
          ].map(({ label, img }, i) => (
            <div
              key={i}
              className='bg-[#e7f1fe] rounded-2xl border border-[#cfe4fc] p-8 max-w-xs'
            >
              <span className='flex justify-between'>
                <input
                  type='checkbox'
                  className='appearance-none w-5 h-5 rounded-full border border-gray-400 checked:bg-[#2f80ed] checked:border-gray-400 transition-colors'
                />
                <Image src={img} width={50} height={50} alt='' />
              </span>
              <div className='text-center'>
                <p className='text-2xl font-bold'>{label}</p>
                <p>
                  النص هنا النص هنا النص هنا النص هنا النص هنا النص هنا النص هنا النص هنا النص هنا
                </p>
              </div>
            </div>
          ))}
        </div>
        <Button
          variant='destructive'
          className='w-64 h-12 flex items-center justify-center gap-2'
        >
          <PaperAirplaneIcon className='text-white w-5 h-5' /> قدم طلب
        </Button>
        <Button
          variant='default'
          className='w-64 h-12'
          onClick={() => setShowPopup(false)}
        >
          تخطى
        </Button>
      </div>
    </div>
  </div>
)}

    </div>
  );
};

export default Partners;
