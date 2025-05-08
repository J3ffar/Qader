import React from "react";
import { UsersIcon } from '@heroicons/react/24/solid';
import Image from "next/image";


const AboutPage = () => {
  return (
    <div className="flex flex-col justify-center items-center gap-7 p-7 dark:bg-[#0B1739]">
      <h2 className="text-5xl font-bold">البداية من حلم...<span className="text-[#E78B48]">والتحقيق معك</span></h2>
      <p className="text-lg max-w-xl text-center">فى عالم تتسارع فيه التحديات وتتشابه فيه المنصات, كنا نبحث عن شئ واحد فقط أن نكون <span className="text-[#E78B48]">مختلفين بحق</span></p>
      <div className="flex justify-center gap-6 p-9 max-md:flex-col max-w-4xl">
        <div className="bg-[#e7f1fe] rounded-3xl flex flex-1/2 flex-col gap-5 justify-center items-center p-4 border border-[#cfe4fc] dark:bg-[#074182]">
         <span className="w-16 h-16 rounded-full flex justify-center items-center bg-[#e7f1fe] shadow-2xl inset-shadow-sm border border-[#9ec9fa]"><Image src={"/images/Storytelling.png"} width={40} height={400} alt="" /></span>
         <p className="text-center text-lg">بدأت<span className="text-[#E78B48]">"قادر"</span>من إيمان بسيط و عميق فى نفس الوقت: أن كل طالب قادر على الإنجاز...غذا وجد البيئةالصحيحةوالدعم المناسب</p>
        </div>
        <div className="bg-[#e7f1fe] rounded-3xl flex flex-1/2 flex-col gap-5 justify-center items-center p-4 border border-[#cfe4fc] dark:bg-[#074182]">
         <span className="w-16 h-16 rounded-full flex justify-center items-center bg-[#e7f1fe] shadow-2xl inset-shadow-sm border border-[#9ec9fa]"><UsersIcon className="w-8 h-8 text-[#172bab]"/></span>
         <p className="text-center text-lg">لم نرد ان نقدم مجرد منصة تعليميةأخرى, بل أردنا أن نبنى مجتمعا<span className="text-[#E78B48]">يتعلم, يشارك, ويكبر سويا.</span></p>
        </div>
        <div className="bg-[#e7f1fe] rounded-3xl flex flex-1/2 flex-col gap-5 justify-center items-center p-4 border border-[#cfe4fc] dark:bg-[#074182]">
         <span className="w-16 h-16 rounded-full flex justify-center items-center bg-[#e7f1fe] shadow-2xl inset-shadow-sm border border-[#9ec9fa]"><Image src={"/images/Greeting.png"} width={55} height={55} alt="" /></span>
         <p className="text-center text-lg">جمعنا بين البساطة و التقنية, بين المناهج الدقيقة و الاختبارات الذكية<span className="text-[#E78B48]">من أجلك أنت.</span></p>
        </div>
      </div>
      <Image src={"/images/phon.png"} width={700} height={700} alt="" />
      <div className="bg-[#e7f1fe] rounded-2xl mx-11 my-9 p-7 dark:bg-[#074182]">
        <div className="flex justify-between items-center gap-20 max-lg:gap-7 max-lg:flex-col-reverse">
          <div>
            <h3 className="text-3xl font-bold">لماذا نحن مختلفون؟</h3>
            <ul className="list-disc list-inside text-right text-lg">
              <li>لأننا نراك قبل أن نرى درجاتك.</li>
              <li>لأننا نفهم أن التعليم ليس بالحفظ, بل فهم وتجربة</li>
              <li>لأننا نطور المنصة كل يوم بناء على صوتك.</li>
              <li>لأننا لا نبيع المحتوى...بل نبنى ثقة.س</li>
            </ul>
          </div>
          <Image src={"/images/labtop.png"} width={500} height={500} alt=""/>
        </div>
        <div className="flex justify-between items-center gap-20 max-lg:gap-7 max-lg:flex-col mt-9">
          <Image src={"/images/labtop1.png"} width={500} height={500} alt="" />
          <div>
            <h3 className="text-3xl font-bold">رسالتنا</h3>
            <ul className="list-disc list-inside text-right text-lg">
              <li>أن نكون دليلك الذكى فى رحلة التعليم, وأن نمنحك الأدوات لتكون دائما...قادر على الفهم, على التقدم, وعلى التميز.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;
