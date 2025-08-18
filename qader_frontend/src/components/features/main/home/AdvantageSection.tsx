"use client";
import React, { useEffect, useRef } from "react";
import Image from "next/image";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import type { HomepageData, Feature } from "@/types/api/content.types";
import img from "../../../../../public/images/photo-1.png";

// Register ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

type AdvantageProps = {
  data: {
    features: Feature[];
    partnerText: HomepageData["why_partner_text"];
  };
};

const AdvantageSection = ({ data }: AdvantageProps) => {
  // Refs for animations
  const sectionRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const featuresRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLDivElement>(null);
  const featureItemsRef = useRef<(HTMLDivElement | null)[]>([]);

  const title =
    data.partnerText?.content_structured_resolved.section_title.value ??
    "لماذا يجب على العملاء أن يختارونا؟";
  const subtitle =
    data.partnerText?.content_structured_resolved?.section_subtitle?.value ??
    "ما الذي يجعلنا نتميز عن المنافسين.";
  const mainImage =
    data.partnerText?.content_structured_resolved?.main_image?.value ?? img;

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states - CHANGED: x: 50 instead of x: -50 (from right)
      gsap.set([titleRef.current, subtitleRef.current], {
        opacity: 0,
        x: 50, // CHANGED: Start from right side
      });

      gsap.set(featureItemsRef.current, {
        opacity: 0,
        x: 30, // CHANGED: Start from right side
        scale: 0.95,
      });

      gsap.set(imageRef.current, {
        opacity: 0,
        scale: 0.8,
        rotation: 5, // CHANGED: Positive rotation for right-side entry
      });

      // Create main timeline
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 120%",
          end: "bottom 25%",
          toggleActions: "play none none reverse",
        },
      });

      // Animate title - slide in from right
      tl.to(titleRef.current, {
        opacity: 1,
        x: 0,
        duration: 0.8,
        ease: "power3.out",
      });

      // Animate subtitle - slide in from right
      tl.to(
        subtitleRef.current,
        {
          opacity: 1,
          x: 0,
          duration: 0.6,
          ease: "power2.out",
        },
        "-=0.5"
      );

      // Animate features with stagger - slide in from right
      tl.to(
        featureItemsRef.current,
        {
          opacity: 1,
          x: 0,
          scale: 1,
          duration: 0.5,
          stagger: 0.1,
          ease: "power2.out",
        },
        "-=0.3"
      );

      // Animate image with rotation - slide in from right
      tl.to(
        imageRef.current,
        {
          opacity: 1,
          scale: 1,
          rotation: 0,
          duration: 1,
          ease: "back.out(1.2)",
        },
        "-=0.8"
      );

      // Add continuous floating animation to image
      gsap.to(imageRef.current, {
        y: -15,
        rotation: 2,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 1.5,
      });

      // Add number counter animation for feature indices
      featureItemsRef.current.forEach((item, index) => {
        if (!item) return;
        
        const numberElement = item.querySelector('.feature-number');
        if (numberElement) {
          gsap.fromTo(
            numberElement,
            { 
              textContent: "0",
              color: "#e78b48"
            },
            {
              textContent: index + 1,
              duration: 1,
              delay: 0.5 + index * 0.1,
              ease: "power2.out",
              snap: { textContent: 1 },
              scrollTrigger: {
                trigger: item,
                start: "top 120%",
                toggleActions: "play none none none",
              },
              onUpdate: function() {
                numberElement.textContent = Math.floor(this.progress() * (index + 1)) + ".";
              }
            }
          );
        }
      });

      // Interactive hover effects for features - CHANGED: x: -10 instead of x: 10 for RTL feel
      featureItemsRef.current.forEach((item, index) => {
        if (!item) return;

        item.addEventListener("mouseenter", () => {
          gsap.to(item, {
            scale: 1.03,
            x: -10, // CHANGED: Move to left on hover for RTL feel
            duration: 0.3,
            ease: "power2.out",
          });

          // Animate the icon/number
          gsap.to(item.querySelector('.feature-number'), {
            scale: 1.2,
            color: "#FDFDFD",
            duration: 0.3,
            ease: "power2.out",
          });
        });

        item.addEventListener("mouseleave", () => {
          gsap.to(item, {
            scale: 1,
            x: 0,
            duration: 0.3,
            ease: "power2.out",
          });

          gsap.to(item.querySelector('.feature-number'), {
            scale: 1,
            color: "inherit",
            duration: 0.3,
            ease: "power2.out",
          });
        });
      });

      // Parallax effect on scroll
      gsap.to(imageRef.current, {
        yPercent: -20,
        ease: "none",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top bottom",
          end: "bottom top",
          scrub: 1,
        },
      });

      // Add subtle pulse to features on scroll
      ScrollTrigger.create({
        trigger: featuresRef.current,
        start: "top 60%",
        onEnter: () => {
          gsap.to(featureItemsRef.current, {
            scale: 1.02,
            duration: 0.3,
            stagger: 0.05,
            yoyo: true,
            repeat: 1,
            ease: "power1.inOut",
          });
        },
      });

    }, sectionRef);

    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, [data.features.length]);

  return (
    <div
      ref={sectionRef}
      className="bg-white dark:bg-[#081028] md:px-20 px-4 overflow-hidden transform-gpu"
    >
      <div className="h-full flex justify-center items-center max-md:flex-col-reverse py-6 container mx-auto px-0 gap-9">
        {/* Text Content Section */}
        <div className="w-full flex-1">
          <h3
            ref={titleRef}
            className="text-4xl font-bold transform-gpu"
            style={{
              textShadow: "0 2px 8px rgba(0,0,0,0.1)",
            }}
          >
            {title}
          </h3>
          <p
            ref={subtitleRef}
            className="text-xl text-gray-600 dark:text-[#D9E1FA] transform-gpu"
          >
            {subtitle}
          </p>
          <div ref={featuresRef} className="flex flex-col gap-3 mt-6">
            {data.features.map((feature, index) => (
              <div
                key={index}
                ref={(el) => {
                  featureItemsRef.current[index] = el;
                }}
                className={`py-2 px-4 rounded-[16px] transition-all delay-150 duration-300 ease-in-out dark:bg-[#0B1739] bg-[#E7F1FE] hover:dark:bg-[#053061] hover:bg-[#074182] hover:text-[#FDFDFD] hover:dark:font-[600] hover:dark:text-[#FDFDFD] cursor-pointer transform-gpu will-change-transform relative overflow-hidden group`}
              >
                {/* Animated background gradient */}
                <div className="absolute inset-0 bg-gradient-to-r from-[#e78b48]/0 via-[#e78b48]/10 to-[#e78b48]/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-out" />
                
                <h2 className="text-2xl font-heading relative z-10">
                  <span className="feature-number inline-block transform-gpu font-bold">
                    {index + 1}.
                  </span>{" "}
                  {feature.title}
                </h2>
                <p className="text-md relative z-10">{feature.text}</p>
                
                {/* Decorative element */}
                <div className="absolute -right-10 top-1/2 -translate-y-1/2 w-20 h-20 bg-[#e78b48]/10 rounded-full blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              </div>
            ))}
          </div>
        </div>
        
        {/* Image Section */}
        <div className="flex flex-1 justify-center">
          <div
            ref={imageRef}
            className="transform-gpu will-change-transform relative"
            style={{ perspective: "1000px" }}
          >
            {/* Glow effect behind image */}
            <div className="absolute inset-0 bg-gradient-to-br from-[#e78b48]/20 to-[#074182]/20 blur-3xl scale-90 opacity-50" />
            
            <Image
              src={mainImage}
              alt="صورة توضيحية للمميزات"
              width={700}
              height={700}
              className="relative z-10 filter drop-shadow-2xl"
              priority
            />
            
            {/* Animated circles around image */}
            <div className="absolute top-10 right-10 w-4 h-4 bg-[#e78b48] rounded-full animate-ping" />
            <div className="absolute bottom-20 left-10 w-3 h-3 bg-[#074182] rounded-full animate-ping animation-delay-200" />
            <div className="absolute top-1/2 right-0 w-2 h-2 bg-[#3D93F5] rounded-full animate-ping animation-delay-400" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvantageSection;
