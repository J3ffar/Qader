import React from 'react';
import { User } from 'lucide-react';

const Review = () => {
    return (
    <div className='p-6'>
        <div>
            <h2 className='text-3xl font-medium'>ماذا قالوا <span className='text-[#074182]'>عنا؟</span></h2>
            <p>ذكر شرح مختصر لعنوان المدح</p>
        </div>
            <div className='flex justify-between max-md:flex-wrap gap-9 mt-7'>
                <div className='w-full shadow-2xl rounded-2xl flex flex-col justify-center items-center border-r-8 p-8 border-r-[#074182] transition delay-150 duration-300 ease-in-out scale-105'>
                    <p className='w-12 h-12 bg-[#ededed] flex justify-center items-center rounded-full'><User className="w-5 h-5 text-[#c9c7c7]" /></p>
                    <h3 className='font-bold'>User Name</h3>
                    <p>description</p>
                    <p className='text-gray-600'>ماذا قال</p>
                </div>
                <div className='w-full shadow-xl rounded-2xl flex flex-col justify-center items-center border-r-8 p-8 border-r-[#e78b48] transition delay-150 duration-300 ease-in-out hover:border-r-[#074182] hover:shadow-2xl hover:scale-105'>
                    <p className='w-12 h-12 bg-[#ededed] flex justify-center items-center rounded-full'><User className="w-5 h-5 text-[#c9c7c7]" /></p>
                    <h3 className='font-bold'>User Name</h3>
                    <p>description</p>
                    <p className='text-gray-600'>ماذا قال</p>
                </div>
                <div className='w-full shadow-xl rounded-2xl flex flex-col justify-center items-center border-r-8 p-8 border-r-[#e78b48] transition delay-150 duration-300 ease-in-out hover:border-r-[#074182] hover:shadow-2xl hover:scale-105'>
                    <p className='w-12 h-12 bg-[#ededed] flex justify-center items-center rounded-full'><User className="w-5 h-5 text-[#c9c7c7]" /></p>
                    <h3 className='font-bold'>User Name</h3>
                    <p>description</p>
                    <p className='text-gray-600'>ماذا قال</p>
                </div>
        </div>    
    </div>
    )
}

export default Review