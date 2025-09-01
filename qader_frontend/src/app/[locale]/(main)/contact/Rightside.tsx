"use client"
import React, { useEffect, useRef } from 'react';
import Image from "next/image";
import Link from "next/link";
import { gsap } from 'gsap';
import {
  EnvelopeIcon,
  PaperAirplaneIcon,
  PhoneIcon,
  LinkIcon,
} from "@heroicons/react/24/solid";
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

const Rightside = ({
  mainImage,
  title,
  description,
  socialsTitle,
  socialLinks
}: any) => {
  // Create refs for animated elements
  const imageRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const descriptionRef = useRef<HTMLParagraphElement>(null);
  const socialsRef = useRef<HTMLDivElement>(null);
  const socialLinksRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const tl = gsap.timeline();

    // Set initial states
    gsap.set([titleRef.current, descriptionRef.current], {
      opacity: 0,
      y: 50,
    });

    gsap.set(imageRef.current, {
      opacity: 0,
      scale: 0.8,
    });

    if (socialLinks.length > 0) {
      gsap.set([socialsRef.current, socialLinksRef.current], {
        opacity: 0,
        y: 30,
      });
    }

    // Animation timeline
    tl.to(imageRef.current, {
      opacity: 1,
      scale: 1,
      duration: 0.8,
      ease: "back.out(1.7)",
    })
    .to(titleRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.6,
      ease: "power2.out",
    }, "-=0.4")
    .to(descriptionRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.6,
      ease: "power2.out",
    }, "-=0.3");

    // Animate social links if they exist
    if (socialLinks.length > 0) {
      tl.to(socialsRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.5,
        ease: "power2.out",
      }, "-=0.2")
      .to(socialLinksRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.5,
        ease: "power2.out",
      }, "-=0.3");
    }

    // Wave animation for image (continuous)
    gsap.to(imageRef.current, {
      rotation: 2,
      duration: 2,
      ease: "sine.inOut",
      yoyo: true,
      repeat: -1,
    });

    // Subtle floating animation for image
    gsap.to(imageRef.current, {
      y: -10,
      duration: 3,
      ease: "sine.inOut",
      yoyo: true,
      repeat: -1,
    });

  }, [socialLinks.length]);

  // Handle social icon hover animations
  const handleSocialHover = (e: React.MouseEvent<HTMLAnchorElement>) => {
    const icon = e.currentTarget.querySelector('svg');
    if (icon) {
      gsap.to(icon, {
        rotation: 360,
        duration: 0.5,
        ease: "power2.out",
      });
    }
  };

  const handleSocialLeave = (e: React.MouseEvent<HTMLAnchorElement>) => {
    const icon = e.currentTarget.querySelector('svg');
    if (icon) {
      gsap.to(icon, {
        rotation: 0,
        duration: 0.3,
        ease: "power2.out",
      });
    }
  };

  return (
    <div className="flex flex-col gap-6 flex-1">
      <div ref={imageRef}>
        <Image
          src={mainImage}
          width={500}
          height={500}
          alt="تواصل معنا"
          className="w-full h-auto max-w-xl mx-auto"
        />
      </div>

      <h2
        ref={titleRef}
        className="text-4xl font-bold max-md:text-center"
        dangerouslySetInnerHTML={{ __html: title }}
      />

      <p 
        ref={descriptionRef}
        className="max-w-xl text-lg leading-relaxed text-gray-700 dark:text-gray-300"
      >
        {description}
      </p>

      {socialLinks.length > 0 && (
        <>
          <h3 
            ref={socialsRef}
            className="font-bold text-2xl mt-4"
          >
            {socialsTitle}
          </h3>
          <div ref={socialLinksRef} className="flex gap-4">
            {socialLinks.map((link: any, index: any) => (
              <Link
                href={link.url}
                key={index}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center w-12 h-12 p-2 rounded-full bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition"
                aria-label={`تواصل معنا عبر ${link.icon_name}`}
                onMouseEnter={handleSocialHover}
                onMouseLeave={handleSocialLeave}
              >
                <SocialIcon iconName={link.icon_name} />
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default Rightside;