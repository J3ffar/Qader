import React from 'react'
import Image from 'next/image'
import { ArrowUpLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

const About = () => {
  return (
    <div className="flex justify-center items-center p-6 gap-7 max-md:flex-col-reverse h-full">
      <div>
        <Image src={"/images/video.png"} alt='' width={600} height={600}/>
      </div>
      <div>
        <h2 className='text-3xl font-medium font'>من نحن؟</h2>
        <p className='text-xl mt-4 text-gray-600'>هنا يمكنك تقديم نفسك و من انت و ما القصة التى تريد ان ترويها عن علامتك التجارية او عملك</p>
        <Button variant="outline" className='mt-4'>
          <span>تعرف علينا اكثر</span>
          <ArrowUpLeft className="w-5 h-5" />
        </Button>
      </div>
    </div>
  )
}

export default About