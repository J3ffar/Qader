import React from "react";
import Image from "next/image";
import Link from "next/link";
import { getContactPageContent } from "@/services/content.service";
import type { SocialLink } from "@/types/api/content.types";

// --- START OF NEW COMPONENT ---
// Import the Heroicons we plan to use
import {
  EnvelopeIcon,
  PaperAirplaneIcon,
  PhoneIcon,
  LinkIcon,
} from "@heroicons/react/24/solid";
import { ContactForm } from "@/components/features/main/contact/ContactForm";
import { Send } from "lucide-react";

// Helper component to render the correct icon based on the name from the API
const SocialIcon = ({ iconName }: { iconName: string | null }) => {
  const iconClass = "h-6 w-6 text-gray-700 dark:text-gray-200";

  switch (iconName) {
    case "EnvelopeIcon":
      return <EnvelopeIcon className={iconClass} />;
    case "PaperAirplaneIcon":
      // Using a different icon for Telegram to avoid confusion with the send button
      return <Send className={iconClass} />;
    case "PhoneIcon":
      return <PhoneIcon className={iconClass} />;
    default:
      // Return a generic link icon as a fallback
      return <LinkIcon className={iconClass} />;
  }
};
// --- END OF NEW COMPONENT ---

const ContactPage = async () => {
  const data = await getContactPageContent();
  const content = data?.content_structured_resolved;

  const mainImage = content?.main_image.value ?? "/images/group.png";
  const title =
    content?.title.value ??
    "لنبق على اتصال, <span class='text-[#074182]'>نحن هنا لمساعدتك!</span>";
  const description =
    content?.description.value ??
    "إذا كان لديك أي استفسار، لا تتردد في التواصل معنا.";
  const socialsTitle = content?.socials_title.value ?? "أو تواصل معنا عبر";
  const socialLinks: SocialLink[] = content?.social_links.value ?? [];

  return (
    <div className="bg-white dark:bg-[#081028] sm:px-0 px-3 py-10">
      <div className="flex justify-center items-center p-4 md:p-8 gap-8 max-lg:flex-col container mx-auto">
        {/* Left Side - Static Content */}
        <div className="flex flex-col gap-6 flex-1">
          <Image
            src={mainImage}
            width={500}
            height={500}
            alt="تواصل معنا"
            className="w-full h-auto max-w-xl mx-auto"
          />
          <h2
            className="text-4xl font-bold max-md:text-center"
            dangerouslySetInnerHTML={{ __html: title }}
          />
          <p className="max-w-xl text-lg leading-relaxed text-gray-700 dark:text-gray-300">
            {description}
          </p>

          {socialLinks.length > 0 && (
            <>
              <h3 className="font-bold text-2xl mt-4">{socialsTitle}</h3>
              <div className="flex gap-4">
                {socialLinks.map((link, index) => (
                  <Link
                    href={link.url}
                    key={index}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center w-12 h-12 p-2 rounded-full bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition"
                    aria-label={`تواصل معنا عبر ${link.icon_name}`}
                  >
                    <SocialIcon iconName={link.icon_name} />
                  </Link>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Right Side - Interactive Form */}
        <div className="flex-1 w-full">
          <ContactForm />
        </div>
      </div>
    </div>
  );
};

export default ContactPage;
