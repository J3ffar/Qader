import React from 'react'
import Image from 'next/image'

const Advantage = () => {
  return (
      <div className='h-full flex justify-center items-center max-md:flex-col-reverse p-6 gap-9'>
          <div className='w-full flex-1/2'>
              <h3 className='text-3xl font-medium'>لماذا يجب على العملاء أن يختارونا؟</h3>
              <p className='text-xl text-gray-600'>ما الذى يجعلنا نتميز عن المنافسين.</p>
              <div className='flex flex-col gap-3 mt-6'>
                  <p className=' p-4 rounded-3xl transition delay-150 duration-300 ease-in-out bg-[#074182] text-white'>1 الميزة الرئيسية1</p>
                  <p className='p-4 bg-[#e7f1fe] rounded-3xl transition delay-150 duration-300 ease-in-out hover:bg-[#074182] hover:text-white'>2 الميزة الرئيسية2</p>
                  <p className='p-4 bg-[#e7f1fe] rounded-3xl transition delay-150 duration-300 ease-in-out hover:bg-[#074182] hover:text-white'>3 الميزة الرئيسية3</p>
                  <p className='p-4 bg-[#e7f1fe] rounded-3xl transition delay-150 duration-300 ease-in-out hover:bg-[#074182] hover:text-white'>4 الميزة الرئيسية4</p>
              </div>
          </div>
          <div className='flex flex-1/2'>
              <Image src={"/images/photo-1.png"} alt='' width={600} height={600}/>
          </div>
    </div>
  )
}

export default Advantage