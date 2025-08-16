"use client";
import React, { useState, useEffect, useRef } from "react";
import Image from "next/image";
import { gsap } from "gsap";
import LoginModal from "@/components/auth/LoginModal";
import SignupModal from "@/components/auth/SignupModal";
import type { HomepageData } from "@/types/api/content.types";
import one from "../../../../../public/images/1.png"
import two from "../../../../../public/images/2.png"
import three from "../../../../../public/images/3.png"
import four from "../../../../../public/images/4.png"
import five from "../../../../../public/images/5.png"
import six from "../../../../../public/images/6.png"
import seven from "../../../../../public/images/7.png"
import eight from "../../../../../public/images/8.png"
import nine from "../../../../../public/images/9.png"
import ten from "../../../../../public/images/10.png"

type HeroProps = {
  data: HomepageData["intro"];
};

const HeroSection = ({ data }: HeroProps) => {
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  
  // Refs for animations
  const heroRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLDivElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const buttonsRef = useRef<HTMLDivElement>(null);
  const mainImageRef = useRef<HTMLDivElement>(null);
  const floatingRefs = useRef<(HTMLDivElement | null)[]>([]);

  const switchToLogin = () => {
    setShowSignup(false);
    setShowLogin(true);
  };

  const switchToSignup = () => {
    setShowLogin(false);
    setShowSignup(true);
  };

  const openSignup = () => {
    setShowSignup(true);
    setShowLogin(false);
  };

  useEffect(() => {
    // Set initial states for performance
    gsap.set([titleRef.current, subtitleRef.current, buttonsRef.current, mainImageRef.current], {
      opacity: 0,
      y: 30
    });

    // Create timeline for main content
    const tl = gsap.timeline({
      defaults: {
        ease: "power3.out",
        duration: 0.8
      }
    });

    // Animate main content
    tl.to(titleRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.6
    })
    .to(subtitleRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.6
    }, "-=0.4")
    .to(buttonsRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.6
    }, "-=0.4")
    .to(mainImageRef.current, {
      opacity: 1,
      y: 0,
      scale: 1,
      duration: 0.8,
      ease: "back.out(1.2)"
    }, "-=0.3");

    // Floating animation for background numbers
    floatingRefs.current.forEach((ref, index) => {
      if (ref) {
        // Random initial animation
        gsap.fromTo(ref, 
          {
            opacity: 0,
            scale: 0.5,
            rotation: -180
          },
          {
            opacity: 0.15,
            scale: 1,
            rotation: 0,
            duration: 1,
            delay: index * 0.1,
            ease: "power2.out"
          }
        );

        // Continuous floating animation
        gsap.to(ref, {
          y: "random(-20, 20)",
          x: "random(-15, 15)",
          rotation: "random(-15, 15)",
          duration: "random(4, 6)",
          repeat: -1,
          yoyo: true,
          ease: "sine.inOut",
          delay: index * 0.2
        });
      }
    });

    // Parallax effect on mouse move (throttled for performance)
    let rafId: number;
    const handleMouseMove = (e: MouseEvent) => {
      if (rafId) cancelAnimationFrame(rafId);
      
      rafId = requestAnimationFrame(() => {
        const { clientX, clientY } = e;
        const moveX = (clientX - window.innerWidth / 2) * 0.01;
        const moveY = (clientY - window.innerHeight / 2) * 0.01;

        floatingRefs.current.forEach((ref, index) => {
          if (ref) {
            gsap.to(ref, {
              x: moveX * (index % 2 === 0 ? 1 : -1),
              y: moveY * (index % 2 === 0 ? -1 : 1),
              duration: 0.5,
              ease: "power2.out",
              overwrite: "auto"
            });
          }
        });
      });
    };

    // Add event listener with throttling
    window.addEventListener("mousemove", handleMouseMove);

    // Cleanup
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      if (rafId) cancelAnimationFrame(rafId);
      gsap.killTweensOf([
        titleRef.current,
        subtitleRef.current,
        buttonsRef.current,
        mainImageRef.current,
        ...floatingRefs.current
      ]);
    };
  }, []);

  const heroTitle =
    data?.content_structured_resolved.hero_title.value ??
    "عندك <span class='text-[#e78b48]'>اختبار قدرات؟</span> ومحتاج مساعدة!!";
  const subtitle =
    data?.content_structured_resolved?.hero_subtitle?.value ??
    "منصتنا مخصصة لك, انت فى الطريق الصحيح. اكتشف كيف يمكن لأدواتنا المبتكرة أن تضعك على طريق النجاح.";
  const promoIcon =
    data?.content_structured_resolved?.promo_icon?.value ??
    "/images/container.png";
  const heroImage =
    data?.content_structured_resolved?.main_hero_image?.value ??
    "/images/photo.png";

  return (
    <div ref={heroRef} className="relative bg-[#F9F9FA] dark:bg-[#0B1739] font-body overflow-hidden">
      <div className="absolute inset-0 pointer-events-none">
        <div ref={(el) => { floatingRefs.current[0] = el; }} className="absolute left-14 top-[25%] will-change-transform z-99">
          <Image
            src={one}
            alt="1"
            className="max-w-full h-auto flex-shrink-0"
            loading="lazy"
          />
        </div>
        <div ref={(el) => { floatingRefs.current[1] = el; }} className="absolute left-[25%] top-[37%] will-change-transform">
          <Image
            src={two}
            alt="2"
            className="max-w-full h-auto flex-shrink-0"
            loading="lazy"
          />
        </div>
        <div ref={(el) => { floatingRefs.current[2] = el; }} className="absolute right-[25%] top-[30%] will-change-transform">
          <Image
            src={three}
            alt="3"
            className="max-w-full h-auto flex-shrink-0"
            loading="lazy"
          />
        </div>
        <div ref={(el) => { floatingRefs.current[3] = el; }} className="absolute left-[8%] top-[50%] will-change-transform">
          <Image
            src={four}
            alt="4"
            className="max-w-full h-auto flex-shrink-0"
            loading="lazy"
          />
        </div>
        <div ref={(el) => { floatingRefs.current[4] = el; }} className="absolute left-[15%] top-[70%] will-change-transform">
          <Image
            src={five}
            alt="5"
            className="max-w-full h-auto flex-shrink-0"
            loading="lazy"
          />
        </div>
        <div ref={(el) => { floatingRefs.current[5] = el; }} className="absolute right-[8%] top-[40%] will-change-transform">
          <Image
            src={six}
            alt="6"
            className="max-w-full h-auto flex-shrink-0"
            loading="lazy"
          />
        </div>
        <div ref={(el) => { floatingRefs.current[6] = el; }} className="absolute right-[12%] top-[55%] will-change-transform">
          <Image
            src={seven}
            alt="7"
            className="max-w-full h-auto flex-shrink-0"
            loading="lazy"
          />
        </div>
        <div ref={(el) => { floatingRefs.current[7] = el; }} className="absolute right-14 top-[25%] will-change-transform">
          <Image
            src={eight}
            alt="8"
            className="max-w-full h-auto flex-shrink-0"
            loading="lazy"
          />
        </div>
        <div ref={(el) => { floatingRefs.current[8] = el; }} className="absolute right-10 top-[80%] will-change-transform">
          <Image
            src={nine}
            alt="9"
            className="max-w-full h-auto flex-shrink-0"
            loading="lazy"
          />
        </div>
        <div ref={(el) => { floatingRefs.current[9] = el; }} className="absolute right-[14%] top-[20px] will-change-transform">
          <Image
            src={ten}
            alt="10"
            className="max-w-full h-auto flex-shrink-0"
            loading="lazy"
          />
        </div>
      </div>
      
      <div className="relative flex justify-center items-center flex-col gap-4 w-full p-6 pt-11 container mx-auto px-10 z-10">
        {/* Title */}
        <div 
          ref={titleRef}
          className="flex justify-center items-center gap-6 text-center py-2 px-4 rounded-[16px] bg-[#FFF] dark:bg-[#D1DBF9] dark:text-black transform-gpu"
        >
          <Image
            src={promoIcon}
            alt="أيقونة قادر"
            width={60}
            height={60}
            className="max-w-full h-auto flex-shrink-0"
          />
          <h1
            className="lg:text-6xl md:text-5xl font-medium max-lg:text-4xl max-md:text-3xl"
            dangerouslySetInnerHTML={{ __html: heroTitle }}
          />
        </div>

        {/* Subtitle */}
        <p 
          ref={subtitleRef}
          className="md:text-xl sm:text-lg text-center max-w-[860px] mx-auto px-5 text-[#333333] dark:text-[#D9E1FA] transform-gpu"
        >
          {subtitle}
        </p>

        {/* Action Buttons */}
        <div 
          ref={buttonsRef}
          className="gap-3 flex items-center mt-5 mb-7 transform-gpu"
        >
          <button
            className="flex justify-center gap-2 min-[1120px]:py-3 sm:w-[180px] w-[100px] p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] font-[600] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer hover:scale-105 active:scale-95 transform-gpu"
            onClick={openSignup}
            onMouseEnter={(e) => {
              gsap.to(e.currentTarget, {
                scale: 1.05,
                duration: 0.2,
                ease: "power2.out"
              });
            }}
            onMouseLeave={(e) => {
              gsap.to(e.currentTarget, {
                scale: 1,
                duration: 0.2,
                ease: "power2.out"
              });
            }}
          >
            <span>اشترك</span>
          </button>
          <a href="/about">
            <button 
              className="flex justify-center gap-2 min-[1120px]:py-2.5 sm:w-[180px] w-[100px] p-2 rounded-[8px] bg-transparent border-[1.5px] border-[#074182] text-[#074182] dark:border-[#3D93F5] dark:text-[#3D93F5] font-[600] hover:bg-[#07418211] dark:hover:bg-[#3D93F511] transition-all cursor-pointer hover:scale-105 active:scale-95 transform-gpu"
              onMouseEnter={(e) => {
                gsap.to(e.currentTarget, {
                  scale: 1.05,
                  duration: 0.2,
                  ease: "power2.out"
                });
              }}
              onMouseLeave={(e) => {
                gsap.to(e.currentTarget, {
                  scale: 1,
                  duration: 0.2,
                  ease: "power2.out"
                });
              }}
            >
              <span>تعرف علينا</span>
            </button>
          </a>
        </div>

        {/* Main Hero Image */}
        <div ref={mainImageRef} className="transform-gpu">
          <Image
            src={heroImage}
            alt="طالب يدرس لاختبار القدرات"
            width={800}
            height={800}
            priority
            className="hover:scale-105 transition-transform duration-500 ease-out"
          />
        </div>
      </div>

      <LoginModal
        show={showLogin}
        onClose={() => setShowLogin(false)}
        onSwitchToSignup={switchToSignup}
      />
      <SignupModal
        show={showSignup}
        onClose={() => setShowSignup(false)}
        onSwitchToLogin={switchToLogin}
      />
    </div>
  );
};

export default HeroSection;
