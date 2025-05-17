import { Button } from '@/components/ui/button'
import { PencilSquareIcon } from '@heroicons/react/24/solid'
import { UserPlusIcon } from 'lucide-react'
import Image from 'next/image'
import React from 'react'

const DetermineLevel = () => {
  return (
    <div className="flex min-h-screen dark:bg-[#081028] text-white">
    <div className="flex-1 flex items-center justify-center flex-col">
        <Image src={"/images/search.png"} width={100} height={100} alt="" />
        <p className="font-semibold text-xl text-black dark:text-white mt-6">حدد مستواك</p>
        <p className="text-gray-500 w-[280px] text-center dark:text-[#D9E1FA]">اختبر مستواك معنا قبل البدء، ليتم بناء نموذج تعليمي شخصي لك يحدد نقاط القوة والضعف، بامكانك اعادة الاختبار اكثر من مرة.  </p>
        <a href="/student/level/questions">
        <Button variant="outline" className="w-48 gap-2 mt-4 border-[2px] hover:border-[2px] font-[700] hover:border-[#074182] dark:hover:border-[#3D93F5] dark:border-[#3D93F5] dark:bg-[#3D93F5] hover:dark:bg-transparent ">
          <PencilSquareIcon className="w-5 h-5" />
          <span>ابدأ تحديد المستوى</span>
        </Button>
        </a>
      </div>
      </div>
  )
}

export default DetermineLevel