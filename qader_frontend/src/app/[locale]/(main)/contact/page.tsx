import React from "react";

import { getContactPageContent } from "@/services/content.service";
import type { SocialLink } from "@/types/api/content.types";

// --- START OF NEW COMPONENT ---
// Import the Heroicons we plan to use

import { ContactForm } from "@/components/features/main/contact/ContactForm";
import Rightside from "./Rightside";


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
        <Rightside mainImage={mainImage} title={title} description={description} socialsTitle={socialsTitle} socialLinks={socialLinks}   />

        {/* Right Side - Interactive Form */}
        <div className="flex-1 w-full">
          <ContactForm />
        </div>
      </div>
    </div>
  );
};

export default ContactPage;
