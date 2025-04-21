import React from "react";
import Image from "next/image";
import type { Metadata } from "next";
import { Button } from "@/components/ui/button";
import Link from "next/link";

// Optional: Add specific metadata for this page
export const metadata: Metadata = {
  title: "قصتنا | منصة قادر",
  description:
    "تعرف على قصة منصة قادر، مهمتنا، ورؤيتنا لمساعدة الطلاب في اختبار القدرات.",
};

const AboutPage = () => {
  return (
    <div className="container mx-auto px-4 py-12 md:py-16">
      {" "}
      {/* Page container */}
      <section className="text-center mb-12 md:mb-16">
        <h1 className="text-4xl md:text-5xl font-bold font-heading mb-4 text-primary">
          قصتنا: شغف بمستقبلكم
        </h1>
        <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto">
          نؤمن في قادر بأن كل طالب يمتلك القدرة على التفوق. وُلدت منصتنا من رغبة
          حقيقية في تمكينكم بالأدوات والمعرفة اللازمة لاجتياز اختبار القدرات
          بثقة وتحقيق طموحاتكم الأكاديمية.
        </p>
      </section>
      <section className="mb-12 md:mb-16">
        <Image
          src="/images/about-hero.jpg" // Replace with your actual image path
          alt="فريق عمل منصة قادر أو صورة تعبيرية عن التعليم"
          width={1200}
          height={500}
          className="rounded-lg object-cover w-full h-auto max-h-[500px] shadow-md" // Style the image
          priority // Load this image early if it's prominent
        />
      </section>
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 items-center mb-12 md:mb-16">
        <div>
          <h2 className="text-3xl font-bold font-heading mb-4 text-secondary-foreground">
            مهمتنا
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            مهمتنا هي توفير تجربة تعليمية شاملة ومبتكرة تجعل الاستعداد لاختبار
            القدرات رحلة ممتعة ومثمرة. نسعى لتقديم محتوى عالي الجودة، أدوات
            تدريب فعالة، ودعم مستمر لمساعدة كل طالب على اكتشاف إمكاناته الكاملة.
            {/* Add more details about your mission */}
          </p>
        </div>
        {/* Optional: Add an image related to the mission */}
        <div className="order-first md:order-last">
          <Image
            src="/images/mission-focus.png" // Replace with relevant image
            alt="أيقونة أو صورة تعبر عن مهمة قادر"
            width={400}
            height={400}
            className="rounded-lg mx-auto"
          />
        </div>
      </section>
      <section className="bg-muted dark:bg-slate-800/50 p-8 md:p-12 rounded-lg mb-12 md:mb-16">
        <h2 className="text-3xl font-bold font-heading mb-6 text-center text-secondary-foreground">
          رؤيتنا
        </h2>
        <p className="text-lg text-center text-muted-foreground leading-relaxed max-w-3xl mx-auto">
          نتطلع لأن نكون الوجهة الأولى والموثوقة لطلاب المملكة العربية السعودية
          في رحلتهم نحو التفوق في اختبار القدرات، وأن نساهم بفعالية في بناء جيل
          واثق ومؤهل لتحقيق رؤية المملكة 2030.
          {/* Add more details about your vision */}
        </p>
      </section>
      {/* Optional: Add a section about your team or values */}
      <section className="mb-12 md:mb-16">
        <h2 className="text-3xl font-bold font-heading mb-6 text-center">
          فريقنا
        </h2>
        <p className="text-lg text-center text-muted-foreground max-w-3xl mx-auto mb-8">
          يقف خلف منصة قادر فريق من الخبراء التربويين والمطورين الملتزمين
          بنجاحكم.
        </p>
        {/* Add team member cards or a general description here */}
      </section>
      {/* Optional: Add a call to action */}
      <section className="text-center">
        <h2 className="text-2xl font-bold mb-4">مستعد لتبدأ رحلتك؟</h2>
        <Button asChild>
          <Link href="/login">انضم إلينا الآن</Link>
        </Button>
      </section>
    </div>
  );
};

export default AboutPage;
