"use client";
import React, { useState, useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import LoginModal from "@/components/auth/LoginModal";
import SignupModal from "@/components/auth/SignupModal";
import type { HomepageData } from "@/types/api/content.types";

// Register ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

type CTAProps = {
  data: HomepageData["call_to_action"];
};

const CallToActionSection = ({ data }: CTAProps) => {
  const [showLogin, setShowLogin] = useState(false);
  const [showSignup, setShowSignup] = useState(false);
  
  // Refs for animations
  const sectionRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

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

  const title =
    data?.content_structured_resolved?.title?.value ??
    "هل أنت مستعد للنجاح في اختبار القدرات؟";
  const subtitle =
    data?.content_structured_resolved?.subtitle?.value ??
    "انضم لآلاف الطلاب الذين حققوا أهدافهم مع منصة قادر. ابدأ رحلتك الآن!";
  const buttonText =
    data?.content_structured_resolved?.button_text?.value ?? "اشتراك";

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set([titleRef.current, subtitleRef.current, buttonRef.current], {
        opacity: 0,
        y: 20,
      });

      // Create timeline for entrance animations
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 80%",
          toggleActions: "play none none reverse",
        },
      });

      // Animate title
      tl.to(titleRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.6,
        ease: "power2.out",
      });

      // Animate subtitle
      tl.to(
        subtitleRef.current,
        {
          opacity: 1,
          y: 0,
          duration: 0.6,
          ease: "power2.out",
        },
        "-=0.3"
      );

      // Animate button with scale effect
      tl.to(
        buttonRef.current,
        {
          opacity: 1,
          y: 0,
          scale: 1,
          duration: 0.6,
          ease: "back.out(1.5)",
        },
        "-=0.3"
      );

      // Add pulse animation to button to draw attention
      gsap.to(buttonRef.current, {
        scale: 1.05,
        duration: 0.8,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 1.5,
      });

      // Add glow effect to button
      gsap.to(buttonRef.current, {
        boxShadow: "0 0 20px rgba(231, 139, 72, 0.4)",
        duration: 1.5,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 1.5,
      });

    }, sectionRef);

    // Button hover animation
    const handleButtonEnter = () => {
      gsap.to(buttonRef.current, {
        scale: 1.1,
        duration: 0.2,
        ease: "power2.out",
        overwrite: "auto",
      });
    };

    const handleButtonLeave = () => {
      gsap.to(buttonRef.current, {
        scale: 1.05,
        duration: 0.2,
        ease: "power2.out",
        overwrite: "auto",
      });
    };

    const buttonElement = buttonRef.current;
    if (buttonElement) {
      buttonElement.addEventListener("mouseenter", handleButtonEnter);
      buttonElement.addEventListener("mouseleave", handleButtonLeave);
    }

    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
      if (buttonElement) {
        buttonElement.removeEventListener("mouseenter", handleButtonEnter);
        buttonElement.removeEventListener("mouseleave", handleButtonLeave);
      }
    };
  }, []);

  return (
    <div
      ref={sectionRef}
      className="bg-[#FDFDFD] dark:bg-[#0B1739] sm:px-0 px-4 overflow-hidden"
    >
      <div className="flex justify-center items-center flex-col py-9 container mx-auto px-0 gap-4 text-center">
        <h2
          ref={titleRef}
          className="text-4xl font-bold transform-gpu"
        >
          {title}
        </h2>
        <p
          ref={subtitleRef}
          className="text-xl max-w-xl transform-gpu"
        >
          {subtitle}
        </p>
        <button
          ref={buttonRef}
          onClick={openSignup}
          className="mt-4 flex justify-center gap-2 min-[1120px]:py-3 sm:w-[280px] w-[180px] p-2 rounded-[8px] bg-[#074182] dark:bg-[#074182] text-[#FDFDFD] hover:bg-[#074182DF] dark:hover:bg-[#074182DF] transition-all cursor-pointer transform-gpu relative overflow-hidden group"
        >
          <span className="relative z-10">{buttonText}</span>
          
          {/* Sweep effect on hover */}
          <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-700 ease-out" />
        </button>
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

export default CallToActionSection;
