import React from 'react'
import Image from 'next/image'

const About = () => {
  return (
      <div>
          <h1>وش يقدم لك قادر؟</h1>
          <div>
              <div className='bg-amber-500 rounded-3xl'>
                  <Image src={"/images/exam.png"} width={50} height={50} alt='' />
                  <div>
                      <h2 className='text-gray-700 text-2xl font-medium'>تدريبات منوعة</h2>
                      <p className='text-gray-500'>تدرب بذكاء على أسئلة تغطي كافة جوانب ومهارات اختبارك لتضمن إتقان المهارات</p>
                  </div>
              </div>
              <div className='bg-amber-500 rounded-3xl'>
                  <Image src={"/images/exam.png"} width={50} height={50} alt='' />
                  <div>
                      <h2 className='text-gray-700 text-2xl font-medium'>تدريبات منوعة</h2>
                      <p className='text-gray-500'>تدرب بذكاء على أسئلة تغطي كافة جوانب ومهارات اختبارك لتضمن إتقان المهارات</p>
                  </div>
              </div>
              <div className='bg-amber-500 rounded-3xl'>
                  <Image src={"/images/exam.png"} width={50} height={50} alt='' />
                  <div>
                      <h2 className='text-gray-700 text-2xl font-medium'>تدريبات منوعة</h2>
                      <p className='text-gray-500'>تدرب بذكاء على أسئلة تغطي كافة جوانب ومهارات اختبارك لتضمن إتقان المهارات</p>
                  </div>
              </div>
              <div className='bg-amber-500 rounded-3xl'>
                  <Image src={"/images/exam.png"} width={50} height={50} alt='' />
                  <div>
                      <h2 className='text-gray-700 text-2xl font-medium'>تدريبات منوعة</h2>
                      <p className='text-gray-500'>تدرب بذكاء على أسئلة تغطي كافة جوانب ومهارات اختبارك لتضمن إتقان المهارات</p>
                  </div>
              </div>
          </div>
    </div>
  )
}

export default About