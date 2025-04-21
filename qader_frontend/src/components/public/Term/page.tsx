import React from 'react'
import { Button } from '@/components/ui/button';


const Term = () => {
  return (
    <div className='flex justify-center items-center flex-col p-8 gap-4'>
          <h2 className='text-3xl font-medium'>عباره تحث المستخدم على اتخاذ اجراء</h2>
          <p className='text-xl'>امنح زوار موقعك طريقة سهله لتحويل او شراء منتجك</p>
          <Button variant="outline">
            <span> اشتراك</span>
          </Button>
    </div>
  )
}

export default Term