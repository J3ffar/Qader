import React from 'react'
import { AcademicCapIcon, BuildingOfficeIcon, UsersIcon,PaperAirplaneIcon } from "@heroicons/react/24/solid";
import Image from "next/image";
import { Button } from "@/components/ui/button";



const Partners = () => {
  return (
      <div className='p-8'>
        <div className="text-center">
                <h2 className="text-4xl font-bold">شركاء النجاح</h2>
                <p className="text-gray-800 text-lg mt-4">لديك سؤال؟ لديناالاجابة, ابحث عن سؤالك هنا.ديك سؤال؟ لديناالاجابة, ابحث عن سؤالك هنا.
                    ديك سؤال؟ لديناالاجابة, ابحث عن سؤالك هنا.
                ديك سؤال؟ لديناالاجابة, ابحث عن سؤالك هنا.</p>
        </div>
        <div className='flex justify-center items-center gap-4 mt-10 max-md:flex-wrap max-sm:flex-col'>
              <div className='flex flex-col gap-4 max-md:flex-1/3 justify-center items-center p-4 bg-[#f7fafe] rounded-3xl border border-[#074182] hover:border-[#56769b] hover:scale-105  transition delay-150 duration-300 ease-in-out'>
                  <Image src={"/images/partner1.png"} width={70} height={70} alt=''/>
                  <h3 className='text-2xl font-bold'>شراكة الطلاب</h3>
                  <p className='text-center'>النص هنا لنص هنالنص هنالنص هنالنص هنالنص هنالنص هنالنص هنالنص هنالنص هنا</p>
                  <Button variant={"outline"}>قدم طلب شراكة <PaperAirplaneIcon className='w-5 h5'/></Button>
              </div>
              <div className='flex flex-col gap-4 max-md:flex-1/3 justify-center items-center p-4 bg-[#f7fafe] rounded-3xl border border-[#074182] hover:border-[#56769b] hover:scale-105  transition delay-150 duration-300 ease-in-out'>
                  <Image src={"/images/partner2.png"} width={70} height={70} alt=''/>
                  <h3 className='text-2xl font-bold'>شراكة المدارس</h3>
                  <p className='text-center'>النص هنا لنص هنالنص هنالنص هنالنص هنالنص هنالنص هنالنص هنالنص هنالنص هنا</p>
                  <Button variant={"outline"}>قدم طلب شراكة <PaperAirplaneIcon className='w-5 h5'/></Button>
              </div>
              <div className='flex flex-col gap-4 max-md:flex-1/3 justify-center items-center p-4 bg-[#f7fafe] rounded-3xl border border-[#074182] hover:border-[#56769b] hover:scale-105  transition delay-150 duration-300 ease-in-out'>
                  <Image src={"/images/partner3.png"} width={70} height={70} alt=''/>
                  <h3 className='text-2xl font-bold'>شراكة الدورات</h3>
                  <p className='text-center'>النص هنا لنص هنالنص هنالنص هنالنص هنالنص هنالنص هنالنص هنالنص هنالنص هنا</p>
                  <Button variant={"outline"}>قدم طلب شراكة <PaperAirplaneIcon className='w-5 h5'/></Button>
              </div>
        </div>
          <div className='flex justify-center items-center gap-7 mt-10 max-md:flex-col-reverse'>
              <div className='flex-1/2'>
                  <h3 className='text-3xl font-bold text-[#074182]'>لماذا الشراكه معنا؟</h3>
                  <p>النص هناالنص هناالنص هناالنص هناالنص هناالنص هناالنص هناالنص  النص هناالنص هناالنص هناالنص هناالنص هناالنص هناالنص هناالنص هناالنص هناهناالنص هناالنص هنارالنص هناالنص هناالنص هناالنص هنا</p>
              </div>
              <div className='flex-1/2 flex justify-center'>
                  <Image src={"/images/logo.png"} width={400} height={400} alt='' />
                </div>
          </div>  
    </div>
  )
}

export default Partners