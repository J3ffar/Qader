import React from 'react'

const Statistics = () => {
  return (
      <div className='flex flex-col justify-center items-center p-9'>
          <h2 className='text-3xl font-medium'>تعرف على أحصائياتنا</h2>
          <p className='text-xl'>قم بتضمين نص متحمس عن الأحصائيات هنا</p>
          <div className='flex justify-center items-center mt-4 gap-9 flex-wrap'>
              <div className='p-14 bg-[#e7f1fe] rounded-lg text-2xl font-bold flex justify-center items-center flex-col border-2 border-[#074182]'>
                  <h3>+5000</h3>
                  <h3>اختبار</h3>
              </div>
              <div className='p-14 bg-[#e7f1fe] rounded-lg text-2xl font-bold flex justify-center items-center flex-col border-2 border-[#074182]'>
                  <h3>+5000</h3>
                  <h3>اختبار</h3>
              </div>
              <div className='p-14 bg-[#e7f1fe] rounded-lg text-2xl font-bold flex justify-center items-center flex-col border-2 border-[#074182]'>
                  <h3>+5000</h3>
                  <h3>اختبار</h3>
              </div>
              
          </div>
    </div>
  )
}

export default Statistics