"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogClose,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import Image from "next/image"; // For tutorial images
import { HelpCircle, Sigma } from "lucide-react";

// For better organization, let's define the tutorial content here.
const TutorialContent = () => (
  <div className="prose prose-sm dark:prose-invert max-w-none space-y-4 rtl:prose-rtl">
    <p>
      تم تصميم محرر النصوص في منصة قادر لجعل إضافة معادلات واضحة واحترافية أمراً
      سهلاً. يرجى اتباع الخطوات التالية.
    </p>

    <h4 className="font-semibold text-3xl">الخطوة 1: فتح محرر المعادلات</h4>
    <ol className="list-decimal space-y-2">
      <li>
        <strong>ضع مؤشر الكتابة</strong> في المكان الذي تريد أن تظهر فيه
        المعادلة.
      </li>
      <li>
        من شريط الأدوات العلوي، انقر على{" "}
        <strong>
          أيقونة المعادلة (
          <Sigma className="inline h-4 w-4 align-middle" />)
        </strong>
        .
      </li>
    </ol>
    <p>
      سيؤدي هذا إلى فتح نافذة "إضافة / تعديل معادلة" التي تحتوي على مربع نصي.
    </p>

    <h4 className="font-semibold text-3xl">
      الخطوة 2: إنشاء المعادلة (الطريقة الأسهل)
    </h4>
    <p>
      نوصي بشدة باستخدام محرر المعادلات المرئي لإنشاء صيغة المعادلة (المعروفة
      باسم LaTeX).
    </p>
    <ol className="list-decimal space-y-2">
      <li>
        داخل نافذة "إضافة / تعديل معادلة"، انقر على الرابط:
        <br />
        <a
          href="https://editor.codecogs.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-blue-600 dark:text-blue-400"
        >
          "استخدم محرر معادلات مرئي (يفتح في نافذة جديدة)"
        </a>
      </li>
      <li>
        سيتم فتح موقع <strong>CodeCogs Equation Editor</strong> في نافذة متصفح
        جديدة. استخدم الأزرار المرئية لكتابة معادلتك.
      </li>
      <li className="flex flex-col items-center">
        <span className="self-start">
          أثناء الكتابة، ستلاحظ أن الموقع يقوم بإنشاء "شيفرة LaTeX" في مربع النص
          بالأسفل.
        </span>
        {/* You can host this image in /public/images */}
        {/* <Image
          src="/images/tutorial/codecogs-editor.png"
          alt="محرر CodeCogs المرئي"
          width={500}
          height={215}
          className="mt-2 rounded-md border"
        /> */}
      </li>
    </ol>

    <h4 className="font-semibold text-3xl">الخطوة 3: نسخ ولصق المعادلة</h4>
    <ol className="list-decimal space-y-2">
      <li>
        بعد الانتهاء، قم <strong>بتحديد ونسخ (Copy)</strong> كامل شيفرة LaTeX
        التي تم إنشاؤها.
      </li>
      <li>ارجع إلى نافذة "إضافة / تعديل معادلة" في منصة قادر.</li>
      <li>
        <strong>الصق (Paste)</strong> الشيفرة في مربع النص المسمى "صيغة LaTeX".
      </li>
      <li>
        انقر على زر <strong>"حفظ المعادلة"</strong>.
      </li>
    </ol>
    <p>
      هذا كل شيء! ستظهر معادلتك الآن منسقة بشكل جميل داخل محرر النصوص الرئيسي.
    </p>

    <hr />

    <h4 className="font-semibold text-3xl">نصائح إضافية</h4>
    <ul className="list-disc space-y-1">
      <li>
        <strong>لتعديل معادلة موجودة:</strong> انقر عليها لتحديدها، ثم انقر على
        أيقونة المعادلة (
        <Sigma className="inline h-4 w-4 align-middle" />) مرة أخرى.
      </li>
      <li>
        <strong>للمستخدمين المتقدمين:</strong> إذا كنت تعرف LaTeX، يمكنك كتابة
        الشيفرة مباشرة في مربع الحوار.
      </li>
    </ul>
  </div>
);

export const EquationTutorialDialog = () => {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="default" size="sm" className="h-auto p-1 text-xs ">
          <HelpCircle className="h-4 w-4 rtl:ml-1 ltr:mr-1" />
          كيفية الاستخدام
        </Button>
      </DialogTrigger>
      <DialogContent className="md:max-w-3xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>دليل: كيفية إضافة المعادلات الرياضية</DialogTitle>
        </DialogHeader>
        <TutorialContent />
        <DialogFooter>
          <DialogClose asChild>
            <Button>فهمت</Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
