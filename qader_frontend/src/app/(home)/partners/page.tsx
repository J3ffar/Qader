"use client";

import React, { useEffect, useState } from "react";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";
import Image from "next/image";

interface PartnerCategory {
  id: number;
  name: string;
  description: string;
  icon_svg_or_class: string;
  google_form_link: string;
}

interface WhyPartnerText {
  title: string;
  content: string;
}

const fallbackPartners: PartnerCategory[] = [
  {
    id: 1,
    name: "شراكة المدارس",
    description: "نساعد المدارس في تقديم دعم مخصص لطلابهم.",
    icon_svg_or_class: "icon-school",
    google_form_link: "#",
  },
  {
    id: 2,
    name: "شراكة الدورات",
    description: "دمج منصة قادر في برامج التدريب الخاصة بك.",
    icon_svg_or_class: "icon-trainer",
    google_form_link: "#",
  },
  {
    id: 3,
    name: "شراكة الطلاب",
    description: "كن سفيرًا لمنصة قادر في مجتمعك.",
    icon_svg_or_class: "icon-student",
    google_form_link: "#",
  },
];

const fallbackWhyPartner: WhyPartnerText = {
  title: "لماذا الشراكة معنا؟",
  content: "نقدم تصميمًا جميلًا وتجربة فريدة لدعم طلابك وتحقيق نتائج أفضل.",
};

const Partners: React.FC = () => {
  const [showPopup, setShowPopup] = useState(false);
  const [isAnySelected, setIsAnySelected] = useState(false);
  const [partnerCategories, setPartnerCategories] = useState<PartnerCategory[]>(fallbackPartners);
  const [whyPartner, setWhyPartner] = useState<WhyPartnerText>(fallbackWhyPartner);

  const handleCheckboxChange = (e: any) => {
    setIsAnySelected(e.target.checked);
  };

  useEffect(() => {
    const fetchPartners = async () => {
      try {
        const res = await fetch("https://qader.vip/ar/api/v1/content/partners/");
        const data = await res.json();
        console.log("📦 Partners Data:", data);

        if (Array.isArray(data.partner_categories)) {
          setPartnerCategories(data.partner_categories);
        }

        if (data.why_partner_text?.title) {
          setWhyPartner(data.why_partner_text);
        }
      } catch (err) {
        console.error("❌ Failed to fetch partners. Using fallback.", err);
        setPartnerCategories(fallbackPartners);
        setWhyPartner(fallbackWhyPartner);
      }
    };

    fetchPartners();
  }, []);

  return (
    <div className="p-8 dark:bg-[#081028]">
      <div className="flex justify-center items-center flex-col container mx-auto">
        <h2 className="text-4xl font-bold">شركاء النجاح</h2>
        <p className="text-gray-800 text-lg max-w-xl mt-4 dark:text-[#D9E1FA]">
          لديك سؤال؟ لدينا الاجابة، ابحث عن سؤالك هنا...
        </p>
      </div>

      <div className="grid  justify-center items-center gap-4 mt-10 md:grid-cols-3 sm:grid-cols-2 grid-cols-1 container mx-auto">
        {partnerCategories.map((partner, i) => (
          <div
            key={partner.id}
            className="flex flex-col gap-4 justify-center items-center p-4 bg-[#f7fafe] rounded-3xl border border-[#074182] hover:border-[#56769b] dark:bg-[#0B1739] hover:scale-105 transition delay-150 duration-300 ease-in-out"
          >
            <Image src={`/images/partner${i + 1}.png`} width={70} height={70} alt="" />
            <h3 className="text-2xl font-bold">{partner.name}</h3>
            <p className="text-center">{partner.description}</p>
            <button
              className="w-full flex justify-center gap-2 min-[1120px]:py-3 p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer"
              onClick={() => setShowPopup(true)}
            >
              قدم طلب شراكة <PaperAirplaneIcon className="w-5 h-5" />
            </button>
          </div>
        ))}
      </div>

      <div className="flex justify-center items-center gap-7 mt-14 max-md:flex-col-reverse">
        <div className="flex-1/2">
          <h3 className="text-3xl font-bold text-[#074182] dark:text-[#FDFDFD]">
            {whyPartner.title}
          </h3>
          <p>{whyPartner.content}</p>
        </div>
        <div className="flex-1/2 flex justify-center">
          <Image src={"/images/logo.png"} width={400} height={400} alt="" />
        </div>
      </div>

      {/* Popup Modal */}
      {showPopup && (
        <div className="fixed inset-0 bg-black/25 flex justify-center items-center z-50">
          <div className="bg-white dark:bg-[#0B1739] p-10 mx-4 max-lg:mx-6 max-lg:p-6 rounded-xl shadow-lg max-w-4xl w-full max-lg:max-h-[90vh] overflow-y-auto">
            <div className="flex flex-col justify-center items-center gap-4">
              <h2 className="text-3xl font-bold">هل تريد تقديم طلب شراكة؟</h2>
              <div className="flex gap-6 max-md:flex-col">
                {partnerCategories.map((partner, i) => (
                  <div
                    key={partner.id}
                    className="bg-[#e7f1fe] dark:bg-transparent rounded-2xl border border-[#cfe4fc] p-8 max-w-xs"
                  >
                    <span className="flex justify-between items-center">
                      <input
                        type="checkbox"
                        className="appearance-none w-5 h-5 bg-white rounded-full border border-gray-400 checked:bg-[#2f80ed] checked:border-gray-400 transition-colors"
                        onChange={handleCheckboxChange}
                      />
                      <Image src={`/images/partner${i + 1}.png`} width={40} height={40} alt="" />
                    </span>
                    <div className="text-center mt-7">
                      <p className="text-2xl font-bold">{partner.name}</p>
                      <p className="mt-3">{partner.description}</p>
                    </div>
                  </div>
                ))}
              </div>

              <button
                className={`flex justify-center gap-2 min-[1120px]:py-3 sm:w-[280px] w-[180px] p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all ${
                  !isAnySelected
                    ? "bg-[#ddd] hover:bg-[#ddd] dark:hover:bg-[#074182] cursor-no-drop dark:text-[#FDFDFD] opacity-55"
                    : ""
                }`}
                disabled={!isAnySelected}
                onClick={() => alert("✅ تم إرسال الطلب بنجاح!")}
              >
                <PaperAirplaneIcon className="text-white w-5 h-5" /> قدم طلب
              </button>

              <button
                className="flex justify-center gap-2 min-[1120px]:py-2.5 sm:w-[280px] w-[180px] p-2 rounded-[8px] bg-transparent border-[1.5px] border-[#074182] text-[#074182] dark:border-[#3D93F5] dark:text-[#3D93F5] font-[600] hover:bg-[#07418211] dark:hover:bg-[#3D93F511] transition-all cursor-pointer"
                onClick={() => setShowPopup(false)}
              >
                تخطى
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Partners;
