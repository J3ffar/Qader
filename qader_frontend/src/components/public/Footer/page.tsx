import React from 'react';
import Image from 'next/image'
import Link from 'next/link';


const Footer = () => {
    const nav = [
  { name: 'الرئيسية', ref: '/'},
  { name: 'قصتنا', ref: '/about' },
  { name: 'شركاء النجاح', ref: '/partners'},
  { name: 'صفحة المذكرة', ref: '/notes'},
  { name: 'الأسئلة الشائعة', ref: '/faq' },
  { name: 'تواصل معنا', ref: '/contact', }
];
    return (
      <>
      <div className='bg-[#074182] p-6 flex justify-center w-screen max-md:flex-col gap-10'>
          <div className='flex-1/2'>
              <div className=''><Image alt='' src={"/images/logo.png"} width={100} height={100}/></div>
              <h3 className='font-bold text-2xl text-white mt-8'>نبذه بسيطه عن قادر وماذا تقدم</h3>
              <div className='flex gap-4 mt-8'>
                  <h3 className='font-bold text-xl text-white'>تابع منصتنا</h3>
                  <span className='flex gap-2 text-white'><Image src={"/images/send-2.png"} alt='' width={30} height={30} className='p-1 rounded-full bg-[#e7f1fe]' /></span>
                  <span className='flex gap-2 text-white'><Image src={"/images/SVG-2.png"} alt='' width={30} height={30} className='p-1 rounded-full bg-[#e7f1fe]' /></span>
                  <span className='flex gap-2 text-white'><Image src={"/images/SVG-1.png"} alt='' width={30} height={30} className='p-1 rounded-full bg-[#e7f1fe]' /></span>
                  <span className='flex gap-2 text-white'><Image src={"/images/SVG.png"} alt='' width={30} height={30} className='p-1 rounded-full bg-[#e7f1fe]' /></span>
                  <span className='flex gap-2 text-white'><Image src={"/images/SVG-4.png"} alt='' width={30} height={30} className='p-1 rounded-full bg-[#e7f1fe]' /></span>
                  <span className='flex gap-2 text-white'><Image src={"/images/SVG-5.png"} alt='' width={30} height={30} className='p-1 rounded-full bg-[#e7f1fe]'/></span>
              </div>
          </div>
          <div className='flex-1/2 flex justify-center gap-7'>
              <div>
                  <h3 className='font-bold text-xl text-white'>الصفحات</h3>
                  <ul className='flex flex-col  text-white'>
                    {nav.map((item, index) => (
                    <li key={index}>
                     <Link
                     href={item.ref}
                    className={`font-bold transition-colors duration-300 hover:text-[#7ba3d8]}`}
                     >
                     {item.name}
                   </Link>
                   </li>
                 ))}
                </ul>
              </div>
              <div className='text-white flex flex-col'>
                  <h3 className='font-bold text-xl'>الشروط والاحكام</h3>
                  <Link href={"/"}>الأسئلة الشائعة</Link>
                  <Link href={"/"}>الشروط و الأحكام</Link>
              </div>
              <div className='text-white flex flex-col'>
                  <h3 className='font-bold text-xl'>تواصل معنا</h3>
                  <Link href={"/"}> تواصل معنا</Link>
              </div>
          </div>
            </div>
            <div className='bg-[#053061] text-white font-medium text-center w-screen'>
             <p>© جميع الحقوق محفوظة 2025</p>
            </div>

            </>
  )
}

export default Footer