import React from "react";
import Image from "next/image";
import Link from "next/link";

// Define nav data outside the component
const footerNavLinks = [
  { name: "الرئيسية", ref: "/" },
  { name: "قصتنا", ref: "/about" },
  { name: "شركاء النجاح", ref: "/partners" },
  { name: "صفحة المذكرة", ref: "/notes" },
  { name: "الأسئلة الشائعة", ref: "/faq" },
  { name: "تواصل معنا", ref: "/contact" },
];

// Define social media links data
const socialLinks = [
  { name: "Telegram", icon: "/images/send-2.png", alt: "Telegram" },
  {
    name: "Social Media 1",
    icon: "/images/SVG-2.png",
    alt: "Social Media Icon 1",
  },
  {
    name: "Social Media 2",
    icon: "/images/SVG-1.png",
    alt: "Social Media Icon 2",
  },
  {
    name: "Social Media 3",
    icon: "/images/SVG.png",
    alt: "Social Media Icon 3",
  },
  {
    name: "Social Media 4",
    icon: "/images/SVG-4.png",
    alt: "Social Media Icon 4",
  },
  {
    name: "Social Media 5",
    icon: "/images/SVG-5.png",
    alt: "Social Media Icon 5",
  },
];

const Footer = () => {
  return (
    <footer className="w-full flex flex-col">
      {" "}
      {/* Use footer tag and let parent handle width */}
      {/* Main Footer Content */}
      <div className="bg-[#074182] p-6 flex justify-center max-md:flex-col gap-10 text-white w-full">
        {/* Left Section (Logo, About, Social) */}
        <div className="flex-1">
          {" "}
          {/* Use flex-1 for better distribution */}
          <div>
            <Image
              alt="Qader Logo"
              src="/images/logo.png" // Ensure this path is correct
              width={100}
              height={100}
            />
          </div>
          <h3 className="font-bold text-2xl mt-8">
            نبذه بسيطه عن قادر وماذا تقدم
          </h3>
          <div className="flex gap-4 mt-8 items-center flex-wrap">
            {" "}
            {/* Added items-center and flex-wrap */}
            <h3 className="font-bold text-xl">تابع منصتنا</h3>
            {socialLinks.map((social) => (
              <a
                key={social.name}
                href="#"
                target="_blank"
                rel="noopener noreferrer"
                aria-label={social.alt}
              >
                {" "}
                {/* Use anchor tags for external links */}
                <span className="flex p-1 rounded-full bg-[#e7f1fe]">
                  <Image
                    src={social.icon}
                    alt={social.alt}
                    width={24} // Adjusted size slightly
                    height={24}
                  />
                </span>
              </a>
            ))}
          </div>
        </div>

        {/* Right Section (Links) */}
        <div className="flex-1 flex justify-center gap-7 max-md:justify-start max-md:mt-6">
          {/* Pages Links */}
          <div>
            <h3 className="font-bold text-xl">الصفحات</h3>
            <ul className="flex flex-col mt-2 space-y-1">
              {" "}
              {/* Added margin and spacing */}
              {footerNavLinks.map((item) => (
                <li key={item.name}>
                  <Link
                    href={item.ref}
                    className="font-bold transition-colors duration-300 hover:text-[#7ba3d8]"
                  >
                    {item.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          {/* Terms Links */}
          <div className="flex flex-col">
            <h3 className="font-bold text-xl">الشروط والاحكام</h3>
            <ul className="flex flex-col mt-2 space-y-1">
              {" "}
              {/* Added margin and spacing */}
              <li>
                <Link href="/faq" className="hover:text-[#7ba3d8]">
                  الأسئلة الشائعة
                </Link>
              </li>{" "}
              {/* Assuming /faq is the correct link */}
              <li>
                <Link href="/terms" className="hover:text-[#7ba3d8]">
                  الشروط و الأحكام
                </Link>
              </li>{" "}
              {/* Assuming /terms is the correct link */}
            </ul>
          </div>
          {/* Contact Links */}
          <div className="flex flex-col">
            <h3 className="font-bold text-xl">تواصل معنا</h3>
            <ul className="flex flex-col mt-2 space-y-1">
              {" "}
              {/* Added margin and spacing */}
              <li>
                <Link href="/contact" className="hover:text-[#7ba3d8]">
                  تواصل معنا
                </Link>
              </li>{" "}
              {/* Assuming /contact is the correct link */}
            </ul>
          </div>
        </div>
      </div>
      {/* Copyright Bar */}
      <div className="bg-[#053061] text-white font-medium text-center py-3 w-full">
        {" "}
        {/* Added padding */}
        <p>© جميع الحقوق محفوظة {new Date().getFullYear()}</p>{" "}
        {/* Dynamic year */}
      </div>
    </footer>
  );
};

export default Footer;
