"use client";

import React, { useState, useEffect, useRef } from "react";
import { PaperAirplaneIcon } from "@heroicons/react/24/solid";
import Image from "next/image";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import PartnersModal from "./PartnersModal";
import type { PartnersPageData } from "@/types/api/content.types";

// Register ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

interface PartnersClientProps {
  data: PartnersPageData | null;
}

const PartnersClient: React.FC<PartnersClientProps> = ({ data }) => {
  const [showPopup, setShowPopup] = useState(false);
  
  // Refs for animations
  const pageRef = useRef<HTMLDivElement>(null);
  const heroTitleRef = useRef<HTMLHeadingElement>(null);
  const heroSubtitleRef = useRef<HTMLParagraphElement>(null);
  const cardsContainerRef = useRef<HTMLDivElement>(null);
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);
  const whySectionRef = useRef<HTMLDivElement>(null);
  const whyTextRef = useRef<HTMLDivElement>(null);
  const whyImageRef = useRef<HTMLDivElement>(null);

  // If data fetching failed on the server, show an error message
  if (!data) {
    return (
      <div className="flex flex-col justify-center items-center h-screen dark:bg-[#081028]">
        <h2 className="text-3xl font-bold">
          عذراً، لم نتمكن من تحميل محتوى الصفحة.
        </h2>
      </div>
    );
  }

  const partnerCategories = data.partner_categories ?? [];
  const pageContent = data.page_content?.content_structured_resolved;

  const heroTitle = pageContent?.hero_title?.value ?? "شركاء النجاح";
  const heroSubtitle =
    pageContent?.hero_subtitle?.value ?? "نؤمن بقوة التعاون لتحقيق أهداف أكبر.";
  const whyPartnerTitle =
    pageContent?.why_partner_title?.value ?? "لماذا الشراكة معنا؟";
  const whyPartnerText =
    pageContent?.why_partner_text?.value ??
    "نقدم تجربة فريدة لدعم طلابك وتحقيق أفضل النتائج.";
  const whyPartnerImage =
    pageContent?.why_partner_image?.value ?? "/images/logo.png";

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set([heroTitleRef.current, heroSubtitleRef.current], {
        opacity: 0,
        y: 30,
      });

      gsap.set(cardRefs.current, {
        opacity: 0,
        y: 50,
        rotateY: -30,
      });

      gsap.set([whyTextRef.current, whyImageRef.current], {
        opacity: 0,
      });

      // Hero section animation
      const heroTl = gsap.timeline({
        defaults: { ease: "power3.out" }
      });

      heroTl
        .to(heroTitleRef.current, {
          opacity: 1,
          y: 0,
          duration: 0.8,
        })
        .to(heroSubtitleRef.current, {
          opacity: 1,
          y: 0,
          duration: 0.6,
        }, "-=0.4");

      // Cards animation with 3D effect
      gsap.to(cardRefs.current, {
        opacity: 1,
        y: 0,
        rotateY: 0,
        duration: 0.8,
        stagger: {
          amount: 0.6,
          from: "start"
        },
        ease: "back.out(1.3)",
        transformPerspective: 1000,
        scrollTrigger: {
          trigger: cardsContainerRef.current,
          start: "top 80%",
        },
      });

      // Interactive hover effects for cards
      cardRefs.current.forEach((card, index) => {
        if (!card) return;

        const icon = card.querySelector('img');
        const button = card.querySelector('button');

        // Mouse move 3D tilt effect
        card.addEventListener('mousemove', (e: MouseEvent) => {
          const rect = card.getBoundingClientRect();
          const x = e.clientX - rect.left - rect.width / 2;
          const y = e.clientY - rect.top - rect.height / 2;
          
          gsap.to(card, {
            rotateY: x * 0.05,
            rotateX: -y * 0.05,
            duration: 0.3,
            ease: "power2.out",
            transformPerspective: 1000,
          });
        });

        card.addEventListener('mouseleave', () => {
          gsap.to(card, {
            rotateY: 0,
            rotateX: 0,
            duration: 0.5,
            ease: "power2.out",
          });
        });

        // Icon bounce animation on card hover
        card.addEventListener('mouseenter', () => {
          gsap.to(icon, {
            scale: 1.2,
            rotation: 360,
            duration: 0.5,
            ease: "back.out(1.5)",
          });
          
          gsap.to(button, {
            scale: 1.05,
            duration: 0.3,
            ease: "power2.out",
          });
        });

        card.addEventListener('mouseleave', () => {
          gsap.to(icon, {
            scale: 1,
            rotation: 0,
            duration: 0.5,
            ease: "power2.out",
          });
          
          gsap.to(button, {
            scale: 1,
            duration: 0.3,
            ease: "power2.out",
          });
        });

        // Add floating animation to cards
        gsap.to(card, {
          y: -5,
          duration: 2 + index * 0.2,
          repeat: -1,
          yoyo: true,
          ease: "sine.inOut",
          delay: index * 0.2,
        });
      });

      // Why Partner section animation
      const whyTl = gsap.timeline({
        scrollTrigger: {
          trigger: whySectionRef.current,
          start: "top 75%",
        },
      });

      whyTl
        .fromTo(whyTextRef.current,
          { 
            opacity: 0, 
            x: -50,
            clipPath: "inset(0 100% 0 0)"
          },
          { 
            opacity: 1, 
            x: 0,
            clipPath: "inset(0 0% 0 0)",
            duration: 0.8, 
            ease: "power2.out" 
          }
        )
        .fromTo(whyImageRef.current,
          { 
            opacity: 0, 
            scale: 0.8,
            rotation: -10
          },
          { 
            opacity: 1, 
            scale: 1,
            rotation: 0,
            duration: 0.8, 
            ease: "back.out(1.5)" 
          },
          "-=0.4"
        );

      // Continuous rotation for why image
      gsap.to(whyImageRef.current, {
        rotation: 5,
        y: -10,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 1,
      });

      // Parallax effect on scroll
      gsap.to(whyImageRef.current, {
        yPercent: -15,
        ease: "none",
        scrollTrigger: {
          trigger: whySectionRef.current,
          start: "top bottom",
          end: "bottom top",
          scrub: 1,
        },
      });

      // Add decorative animated particles
      const createParticle = () => {
        const particle = document.createElement('div');
        particle.className = 'particle';
        pageRef.current?.appendChild(particle);
        
        const startX = Math.random() * window.innerWidth;
        const startY = window.innerHeight + 50;
        
        gsap.set(particle, {
          position: 'fixed',
          width: '6px',
          height: '6px',
          backgroundColor: Math.random() > 0.5 ? '#074182' : '#e78b48',
          borderRadius: '50%',
          left: startX,
          top: startY,
          opacity: 0.6,
          zIndex: 0,
        });

        gsap.to(particle, {
          y: -window.innerHeight - 100,
          x: `random(-100, 100)`,
          opacity: 0,
          duration: `random(8, 12)`,
          ease: "none",
          onComplete: () => particle.remove(),
        });
      };

      // Create particles periodically
      const particleInterval = setInterval(createParticle, 1000);

      // Add shine effect to cards periodically
      const addShineEffect = () => {
        cardRefs.current.forEach((card, index) => {
          if (!card) return;
          
          setTimeout(() => {
            const shine = document.createElement('div');
            shine.className = 'shine-effect';
            card.appendChild(shine);
            
            gsap.set(shine, {
              position: 'absolute',
              top: 0,
              left: '-100%',
              width: '100%',
              height: '100%',
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
              pointerEvents: 'none',
            });

            gsap.to(shine, {
              left: '100%',
              duration: 0.8,
              ease: "power2.out",
              onComplete: () => shine.remove(),
            });
          }, index * 200);
        });
      };

      // Trigger shine effect periodically
      const shineInterval = setInterval(addShineEffect, 5000);

      // Cleanup
      return () => {
        clearInterval(particleInterval);
        clearInterval(shineInterval);
      };
    }, pageRef);

    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, [partnerCategories.length]);

  return (
    <div ref={pageRef} className="p-8 dark:bg-[#081028] overflow-hidden transform-gpu">
      <div className="flex justify-center items-center flex-col container mx-auto text-center">
        <h2 
          ref={heroTitleRef}
          className="text-4xl font-bold transform-gpu"
          style={{ textShadow: "0 2px 10px rgba(0,0,0,0.1)" }}
        >
          {heroTitle}
        </h2>
        <p 
          ref={heroSubtitleRef}
          className="text-gray-800 text-lg max-w-xl mt-4 dark:text-[#D9E1FA] transform-gpu"
        >
          {heroSubtitle}
        </p>
      </div>

      <div 
        ref={cardsContainerRef}
        className="grid justify-center items-center gap-4 mt-10 md:grid-cols-3 sm:grid-cols-2 grid-cols-1 container mx-auto md:px-8"
      >
        {partnerCategories.map((partner, index) => {
          const defaultIcon = `/images/partner${index + 1}.png`;
          const iconSrc = partner.icon_image ?? defaultIcon;

          return (
            <div
              key={partner.id}
              // ref={(el) => { cardRefs.current[index] = el; }}
              className="flex flex-col gap-4 justify-center items-center p-4 bg-[#f7fafe] rounded-3xl border border-[#cfe4fc] dark:border-gray-700 hover:border-[#56769b] dark:bg-[#0B1739] transition delay-150 duration-300 ease-in-out text-center cursor-pointer transform-gpu will-change-transform relative overflow-hidden"
              style={{
                transformStyle: "preserve-3d",
                perspective: "1000px",
              }}
            >
              {/* Animated background gradient */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#074182]/0 via-[#e78b48]/5 to-[#074182]/0 opacity-0 hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
              
              <Image 
                src={iconSrc} 
                width={70} 
                height={70} 
                alt={partner.name}
                className="relative z-10 transform-gpu"
              />
              <h3 className="text-2xl font-bold relative z-10">{partner.name}</h3>
              <p className="relative z-10">{partner.description}</p>
              <button
                onClick={() => setShowPopup(true)}
                className="w-full mt-auto flex justify-center gap-2 py-3 px-2 rounded-lg bg-[#074182] text-[#FDFDFD] font-semibold hover:bg-[#053061] transition-all relative z-10 overflow-hidden group transform-gpu"
              >
                <span className="relative z-10">قدم طلب شراكة</span>
                <PaperAirplaneIcon className="w-5 h-5 relative z-10 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform duration-300" />
                
                {/* Button shine effect */}
                <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-700 ease-out" />
              </button>
            </div>
          );
        })}
      </div>

      {/* "Why Partner" section */}
      <div 
        ref={whySectionRef}
        className="flex justify-center items-center gap-14 mt-20 max-md:flex-col-reverse px-8"
      >
        <div ref={whyTextRef} className="flex-1 transform-gpu">
          <h3 className="text-3xl font-bold text-[#074182] dark:text-[#FDFDFD]">
            {whyPartnerTitle}
          </h3>
          <p className="mt-4 text-lg leading-relaxed">{whyPartnerText}</p>
        </div>
        <div ref={whyImageRef} className="flex-1 flex justify-center transform-gpu will-change-transform">
          <Image
            src={whyPartnerImage}
            width={400}
            height={400}
            alt={whyPartnerTitle}
            className="filter drop-shadow-2xl hover:scale-110 transition-transform duration-500"
          />
        </div>
      </div>

      <PartnersModal
        partnerCategories={partnerCategories}
        show={showPopup}
        onClose={() => setShowPopup(false)}
      />
    </div>
  );
};

export default PartnersClient;
