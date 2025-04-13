import { Button } from '@/components/ui/button';
import React from 'react'

const Head = () => {
  return (
    <div className='flex gap-11 p-14 max-md:flex-col-reverse max-md:p-7'>
          <div className='text-center flex-1'>
            <h1 className='text-5xl font-medium text-[#4f008d] max-md:text-3xl'>حياك في موقعنا !</h1>
            <p className='text-2xl font-medium text-[#ff375e] mt-4 max-md:text-lg'>المنصة اللي تدربك على القدرات بذكاء</p>
            <p className='text-2xl text-gray-600 mt-4 max-md:text-lg'>منصة اختبارات تحلل نتائجك في التدريبات، وتوريك النقاط اللي أنت قوي فيها والنقاط اللي تحتاج تدريب ومراجعة، وبنساعدك تقوي نقاط ضعفك في تدريباتك الجاية لين تتحسن. ومو بس كذا! بنتوقع درجتك في الاختبار الحقيقي بناء على تحليلنا لمستواك.</p>
              <Button variant="secondary" className='px-7 py-7 mt-5 ml-4'>تدرب على اختبار القدرات</Button> 
              <Button variant="secondary"  className='px-7 py-7 mt-5'>تدرب على اختبار التحصيلي</Button> 
        </div>
          <div className='flex-1 mr-16 flex max-md:items-center max-md:mr-0 max-md:justify-center'>
              <iframe 
  width="350" 
  height="200" 
  src="https://www.youtube.com/embed/VIDEO_ID" 
  title="YouTube video player" 
  frameBorder="0" 
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
  allowFullScreen
></iframe>
        </div>
    </div>
  )
}

export default Head;