"use client"
import React, { useState } from 'react';
import { JSX } from 'react/jsx-runtime';

type TabKey = 'terms' | 'privacy';

type TabData = {
  title: string;
  content: JSX.Element;
  text: JSX.Element;
};

const ConditionPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('terms');

  const tabs: Record<TabKey, TabData> = {
    terms: {
      title: 'الشروط والأحكام',
      content: (
        <ul className="space-y-3 text-lg text-gray-800">
          <li className="text-[#2F80ED] cursor-pointer">1. الموافقة على الشروط</li>
          <li className="text-[#2F80ED] cursor-pointer">2. نبذة عن موقع "قادر"</li>
          <li className="text-[#2F80ED] cursor-pointer">3. أهلية الاستخدام</li>
          <li className="text-[#2F80ED] cursor-pointer">4. إنشاء الحساب</li>
          <li className="text-[#2F80ED] cursor-pointer">5. الأشتراكات و الخطط المدفوعة</li>
          <li className="text-[#2F80ED] cursor-pointer">6. المحتوى و حقوق الملكية الفكرية</li>
          <li className="text-[#2F80ED] cursor-pointer">7. استخدام المحتوى</li>
          <li className="text-[#2F80ED] cursor-pointer">8. سياسة الخصوصية</li>
          <li className="text-[#2F80ED] cursor-pointer">9. السلوك المحظور</li>
          <li className="text-[#2F80ED] cursor-pointer">10. التعليقات والمساهمات من المستخدمين</li>
        </ul>
      ),
      text: (
        <div className="space-y-6 text-base text-gray-900 leading-loose dark:text-gray-100">
          <p><strong>أولاً: تاريخ السريان</strong><br />تسري هذه الشروط اعتبارا من: (تاريخ يحدد لاحقا)</p>
          <p><strong>ثانيًا:</strong><br />تمثل هذه الاتفاقية عقدًا قانونيًّا بينكم كطرف أول وبين (اسم) المالك لموقع 'قادر' كطرف ثانٍ.</p>
          <p><strong>1. الموافقة على الشروط</strong><br />باستخدامك لموقع "قادر"، فإنك توافق على الالتزام بهذه الشروط.</p>
          <p><strong>2. نبذة عن موقع "قادر"</strong><br />"قادر" منصة تعليمية تقدم محتوى تفاعلي لاختبارات القدرات العامة.</p>
          <p><strong>3. أهلية الاستخدام</strong><br />• لا يُسمح لمن هم دون 13 عامًا باستخدام الموقع.<br />• من هم دون 18 عامًا يجب أن يستخدموا الموقع تحت إشراف ولي أمر.</p>
          <p><strong>4. إنشاء الحساب</strong><br />• قد يتطلب استخدام بعض الخدمات إنشاء حساب.<br />• يجب تقديم معلومات صحيحة.<br />• مسؤوليتك الحفاظ على سرية بيانات الدخول.</p>
          <p><strong>5. الاشتراكات والخطط المدفوعة</strong><br />• المحتوى المدفوع متاح طوال فترة الاشتراك فقط.<br />• لا يمكن استرداد المبالغ.<br />• الأسعار قابلة للتغيير.</p>
          <p><strong>6. المحتوى وحقوق الملكية الفكرية</strong><br />• المحتوى محمي بموجب قوانين حقوق النشر.<br />• لا يجوز نسخ أو إعادة توزيع المحتوى.</p>
          <p><strong>7. استخدام المحتوى</strong><br />• للاستخدام الشخصي فقط.<br />• يُمنع استخدامه لأغراض غير قانونية أو تجارية خارج المنصة.</p>
          <p><strong>8. السلوك المحظور</strong><br />• يُمنع تحميل محتوى غير قانوني أو خادع.<br />• يُمنع اختراق أو محاولة التأثير على أمان الموقع.</p>
          <p><strong>9. التعليقات والمساهمات</strong><br />• أنت مسؤول عن محتوى تعليقاتك.<br />• الموقع يحتفظ بحق حذف أو تعديل أي محتوى مخالف.</p>
        </div>
      ),
    },
    privacy: {
      title: 'سياسة الخصوصية',
      content: (
        <ul className="space-y-3 text-lg text-gray-800 dark:text-gray-200">
          <li className="text-[#2F80ED] cursor-pointer">1. سياسة الخصوصية</li>
          <li className="text-[#2F80ED] cursor-pointer">2. ملفات تعريف الأرتباط (Cookies)</li>
          <li className="text-[#2F80ED] cursor-pointer">3. التنصل من الضمانات</li>
          <li className="text-[#2F80ED] cursor-pointer">4. تحديد المسؤلية</li>
          <li className="text-[#2F80ED] cursor-pointer">5. الروبط  الخارجية</li>
          <li className="text-[#2F80ED] cursor-pointer">6. إنهاء الخدمة</li>
          <li className="text-[#2F80ED] cursor-pointer">7. القانون المعمول به</li>
        </ul>
      ),
      text: (
        <div className="space-y-6 text-gray-900 leading-loose dark:text-gray-100">
          <p><strong>1- سياسة الخصوصية</strong><br />نحن نحترم خصوصيتك ونتعهد بحماية بياناتك. باستخدامك للموقع، فإنك توافق على جمع واستخدام معلوماتك وفقًا لسياسة الخصوصية الخاصة بنا، والتي تشمل:</p>
          <p>• جمع بيانات مثل الاسم، البريد الإلكتروني، الموقع الجغرافي، وسجل الاستخدام.<br />• استخدام البيانات لتحسين تجربة المستخدم وتقديم محتوى مخصص.<br />• عدم مشاركة بياناتك مع أي طرف ثالث إلا في حالة الضرورة القانونية أو لتحسين خدماتنا.<br />• تأمين بياناتك عبر بروتوكولات حماية حديثة.</p>
          <p><strong>2- ملفات تعريف الارتباط (Cookies)</strong><br />• يستخدم موقعنا ملفات تعريف الارتباط لتحسين تجربة المستخدم.<br />• باستخدامك للموقع، فإنك توافق على استخدام ملفات الكوكيز بما يتماشى مع سياسة الخصوصية الخاصة بنا.</p>
          <p><strong>3- التنصل من الضمانات</strong><br />• يتم تقديم الخدمات كما هي دون أي ضمانات.<br />• لا نضمن أن الموقع سيعمل دون أخطاء أو فيروسات.<br />• أنت تتحمل المسؤولية الكاملة عن استخدامك للموقع.</p>
          <p><strong>4- تحديد المسؤولية</strong><br />• لا يتحمل الموقع المسؤولية عن أي خسائر ناتجة عن استخدامه.<br />• أقصى مسؤولية علينا هي قيمة الاشتراك المدفوع خلال آخر 3 أشهر.</p>
          <p><strong>5- الروابط الخارجية</strong><br />قد يحتوي الموقع على روابط لمواقع خارجية لسنا مسؤولين عنها.</p>
          <p><strong>6- التعديلات على الشروط</strong><br />نحتفظ بالحق في تعديل هذه الشروط في أي وقت. استمرارك في استخدام الموقع يُعد قبولاً للتعديلات.</p>
          <p><strong>7- إنهاء الخدمة</strong><br />• يمكننا إنهاء حسابك إذا انتهكت الشروط.<br />• يمكنك إغلاق حسابك من الإعدادات في أي وقت.</p>
          <p><strong>القانون المعمول به</strong><br />تخضع هذه الشروط لقوانين المملكة العربية السعودية.</p>
          <p><strong>التواصل معنا</strong><br />لأي استفسار، يمكنك التواصل معنا عبر البريد الإلكتروني.</p>
          <p className='font-bold'>جميع الحقوق محفوظة © 2025 موقع قادر (Qader)</p>
        </div>
      ),
    },
  };

  return (
    <div className="flex flex-col md:flex-row p-6 md:p-10 gap-8 text-right dark:bg-[#081028]">
      {/* Sidebar */}
      <div className="md:w-1/3 bg-white dark:bg-[#0B1739] p-4 rounded-xl shadow">
        <div className="flex justify-between border-b mb-4 px-2">
          <button
            onClick={() => setActiveTab('terms')}
            className={`text-xl font-bold pb-1 cursor-pointer ${
              activeTab === 'terms' ? 'text-[#074182] dark:text-[#3D93F5] border-b-2 border-[#074182] dark:border-[#3D93F5]' : 'text-gray-700 dark:text-[#D9E1FA]'
            }`}
          >
            الشروط والأحكام
          </button>
          <button
            onClick={() => setActiveTab('privacy')}
            className={`text-lg font-bold pb-1 cursor-pointer ${
              activeTab === 'privacy' ? 'text-[#074182] dark:text-[#3D93F5] border-b-2 border-[#074182] dark:border-[#3D93F5]' : 'text-gray-700 dark:text-[#D9E1FA]'
            }`}
          >
            سياسة الخصوصية
          </button>
        </div>
        <p className="text-lg font-bold text-gray-800 dark:text-[#D9E1FA] mb-4 text-center">جدول المحتويات</p>
        {tabs[activeTab].content}
      </div>

      {/* Content */}
      <div className="md:w-2/3 bg-gray-100 p-6 rounded-xl shadow dark:bg-[#0B1739]">
        {tabs[activeTab].text}
      </div>
    </div>
  );
};

export default ConditionPage;
