import { Button } from '@/components/ui/button';
import Image from 'next/image'
import React from 'react'


const Head = () => {
  return (
    <div className='flex justify-center items-center flex-col gap-8 mt-11 w-full p-6'>
      <div className='flex justify-center items-center gap-4 p-6'>
        <Image src={"/images/container.png"} alt='' width={60} height={60} className='max-w-full h-auto' />
        <h1 className='text-5xl font-medium max-lg:text-4xl max-md:text-3xl'>عندك <span className='text-[#e78b48]'>اختبار قدرات؟</span>ومحتاج مساعدة!!</h1>
      </div>
      <p className='text-xl text-center font-[IBM_Plex_sans]'>  انت فى الطريق الصحيح. انت فى الطريق الصحيح.منصتنا مخصصة لك, انت فى الطريق الصحيح.منصتنا مخصصة لك, انت فى الطريق الصحيح</p>
      <div className='gap-3 flex items-center'>      
        <Button variant="outline">
          <span> اشتراك</span>
        </Button>
      <Button variant="default">
        <span>تعرف علينا</span>
        </Button>
  
      </div>
    <Image src={'/images/photo.png'} alt='image' width={800} height={800}/>
    </div>
  )
}

export default Head;