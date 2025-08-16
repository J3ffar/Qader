"use client";
import React, { useEffect, useRef } from "react";
import Image from "next/image";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  UsersIcon,
  BookOpenIcon,
  SparklesIcon,
} from "@heroicons/react/24/solid";

// Register ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

// Icon component remains the same
const StoryCardIcon = ({ index }: { index: number }) => {
  const iconClass = "w-8 h-8 text-[#172bab]";
  switch (index) {
    case 0:
      return <BookOpenIcon className={iconClass} />;
    case 1:
      return <UsersIcon className={iconClass} />;
    case 2:
      return <SparklesIcon className={iconClass} />;
    default:
      return null;
  }
};

type AboutPageProps = {
  data: any; // Replace with proper type from your content service
};

const AboutPageClient = ({ data }: AboutPageProps) => {
  // Refs for animations
  const pageRef = useRef<HTMLDivElement>(null);
  const heroTitleRef = useRef<HTMLHeadingElement>(null);
  const heroSubtitleRef = useRef<HTMLParagraphElement>(null);
  const storyCardsRef = useRef<(HTMLDivElement | null)[]>([]);
  const mainImageRef = useRef<HTMLDivElement>(null);
  const detailsSectionRef = useRef<HTMLDivElement>(null);
  const whyDifferentRef = useRef<HTMLDivElement>(null);
  const missionRef = useRef<HTMLDivElement>(null);
  const whyImageRef = useRef<HTMLDivElement>(null);
  const missionImageRef = useRef<HTMLDivElement>(null);

  const content = data.content_structured_resolved;
  const mainPromoImage = content.main_promo_image?.value ?? "/images/phon.png";
  const whyDifferentImage =
    content.why_different_image?.value ?? "/images/labtop.png";
  const missionImage = content.mission_image?.value ?? "/images/labtop1.png";

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set([heroTitleRef.current, heroSubtitleRef.current], {
        opacity: 0,
        y: 30,
      });

      gsap.set(storyCardsRef.current, {
        opacity: 0,
        y: 50,
        scale: 0.9,
      });

      gsap.set(mainImageRef.current, {
        opacity: 0,
        scale: 0.8,
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

      // Story cards animation with stagger
      gsap.to(storyCardsRef.current, {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.8,
        stagger: 0.2,
        ease: "back.out(1.5)",
        scrollTrigger: {
          trigger: storyCardsRef.current[0],
          start: "top 80%",
        },
      });

      // Icon rotation animation on hover
      storyCardsRef.current.forEach((card) => {
        if (!card) return;
        
        const icon = card.querySelector('.icon-wrapper');
        
        card.addEventListener('mouseenter', () => {
          gsap.to(icon, {
            rotation: 360,
            scale: 1.1,
            duration: 0.5,
            ease: "power2.out"
          });
          gsap.to(card, {
            scale: 1.05,
            boxShadow: "0 20px 40px rgba(7, 65, 130, 0.15)",
            duration: 0.3,
            ease: "power2.out"
          });
        });
        
        card.addEventListener('mouseleave', () => {
          gsap.to(icon, {
            rotation: 0,
            scale: 1,
            duration: 0.5,
            ease: "power2.out"
          });
          gsap.to(card, {
            scale: 1,
            boxShadow: "none",
            duration: 0.3,
            ease: "power2.out"
          });
        });
      });

      // Main image animation
      gsap.to(mainImageRef.current, {
        opacity: 1,
        scale: 1,
        duration: 1,
        ease: "power3.out",
        scrollTrigger: {
          trigger: mainImageRef.current,
          start: "top 75%",
        },
      });

      // Floating animation for main image
      gsap.to(mainImageRef.current, {
        y: -20,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 1,
      });

      // Details section animation
      gsap.fromTo(detailsSectionRef.current,
        {
          opacity: 0,
          y: 40,
        },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          ease: "power2.out",
          scrollTrigger: {
            trigger: detailsSectionRef.current,
            start: "top 80%",
          },
        }
      );

      // Why different section animation
      const whyTl = gsap.timeline({
        scrollTrigger: {
          trigger: whyDifferentRef.current,
          start: "top 75%",
        },
      });

      whyTl
        .fromTo(whyDifferentRef.current,
          { opacity: 0, x: -50 },
          { opacity: 1, x: 0, duration: 0.8, ease: "power2.out" }
        )
        .fromTo(whyImageRef.current,
          { opacity: 0, x: 50, rotation: -5 },
          { opacity: 1, x: 0, rotation: 0, duration: 0.8, ease: "power2.out" },
          "-=0.4"
        );

      // Animate list items with stagger
      const listItems = whyDifferentRef.current?.querySelectorAll('li');
      if (listItems) {
        gsap.fromTo(listItems,
          { opacity: 0, x: -20 },
          {
            opacity: 1,
            x: 0,
            duration: 0.5,
            stagger: 0.1,
            ease: "power2.out",
            scrollTrigger: {
              trigger: whyDifferentRef.current,
              start: "top 70%",
            },
          }
        );
      }

      // Mission section animation
      const missionTl = gsap.timeline({
        scrollTrigger: {
          trigger: missionRef.current,
          start: "top 75%",
        },
      });

      missionTl
        .fromTo(missionImageRef.current,
          { opacity: 0, x: -50, rotation: 5 },
          { opacity: 1, x: 0, rotation: 0, duration: 0.8, ease: "power2.out" }
        )
        .fromTo(missionRef.current,
          { opacity: 0, x: 50 },
          { opacity: 1, x: 0, duration: 0.8, ease: "power2.out" },
          "-=0.4"
        );

      // Parallax effect on images
      [whyImageRef.current, missionImageRef.current].forEach((img) => {
        gsap.to(img, {
          yPercent: -10,
          ease: "none",
          scrollTrigger: {
            trigger: img,
            start: "top bottom",
            end: "bottom top",
            scrub: 1,
          },
        });
      });

      // Add decorative floating elements
      const createFloatingDot = () => {
        const dot = document.createElement('div');
        dot.className = 'floating-dot';
        pageRef.current?.appendChild(dot);
        
        gsap.set(dot, {
          position: 'fixed',
          width: '4px',
          height: '4px',
          backgroundColor: '#e78b48',
          borderRadius: '50%',
          left: `${Math.random() * 100}%`,
          top: `${Math.random() * 100}%`,
          opacity: 0.3,
          zIndex: 0,
        });

        gsap.to(dot, {
          y: -100,
          opacity: 0,
          duration: 3,
          ease: "power1.out",
          onComplete: () => dot.remove(),
        });
      };

      // Create floating dots periodically
      const dotInterval = setInterval(createFloatingDot, 2000);

      return () => {
        clearInterval(dotInterval);
      };
    }, pageRef);

    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, [content]);

  if (!data) {
    return (
      <div className="flex flex-col justify-center items-center h-screen dark:bg-[#081028]">
        <h2 className="text-3xl font-bold">
          عذراً، لم نتمكن من تحميل محتوى الصفحة.
        </h2>
        <p className="text-lg mt-4">يرجى المحاولة مرة أخرى لاحقاً.</p>
      </div>
    );
  }

  return (
    <div ref={pageRef} className="flex flex-col justify-center items-center gap-7 p-7 dark:bg-[#081028] sm:px-0 px-4 overflow-hidden transform-gpu">
      <h2
        ref={heroTitleRef}
        className="text-5xl font-bold text-center transform-gpu"
        dangerouslySetInnerHTML={{ __html: content.hero_title.value }}
        style={{ textShadow: "0 2px 10px rgba(0,0,0,0.1)" }}
      />
      <p
        ref={heroSubtitleRef}
        className="text-lg max-w-xl text-center transform-gpu"
        dangerouslySetInnerHTML={{ __html: content.hero_subtitle.value }}
      />

      {/* Story Cards Section */}
      <div className="flex justify-center gap-6 p-9 max-md:flex-col max-w-4xl mx-auto">
        {content.story_cards.value.map((card: any, index: number) => (
          <div
            key={index}
            ref={(el) => { storyCardsRef.current[index] = el; }}
            className="bg-[#E7F1FE]/30 rounded-3xl flex flex-1 flex-col gap-5 justify-center items-center p-4 border border-[#9EC9FA] dark:bg-[#0B1739] cursor-pointer transform-gpu will-change-transform relative overflow-hidden group"
          >
            {/* Animated background gradient */}
            <div className="absolute inset-0 bg-gradient-to-br from-[#78B5FF]/0 via-[#D3E8FF]/10 to-[#78B5FF]/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            
            <div className="inline-flex rounded-full bg-gradient-to-b from-[#78B5FF] to-[#D3E8FF] p-[3px] relative z-10">
              <span className="icon-wrapper w-16 h-16 rounded-full flex justify-center items-center bg-[#e7f1fe] transform-gpu">
                <StoryCardIcon index={index} />
              </span>
            </div>
            <p
              className="text-center text-lg relative z-10"
              dangerouslySetInnerHTML={{ __html: card.text }}
            />
          </div>
        ))}
      </div>

      {/* Main Promo Image */}
      <div ref={mainImageRef} className="transform-gpu will-change-transform">
        <Image
          src={mainPromoImage}
          width={700}
          height={700}
          alt="عرض تطبيق قادر"
          className="filter drop-shadow-2xl"
        />
      </div>

      {/* Details Section */}
      <div ref={detailsSectionRef} className="bg-[#E7F1FE4D] rounded-2xl mx-11 my-9 p-7 dark:bg-[#0B1739] transform-gpu">
        {/* Why Different Section */}
        <div className="flex justify-between items-center gap-20 max-lg:gap-7 max-lg:flex-col-reverse">
          <div ref={whyDifferentRef} className="transform-gpu">
            <h3 className="text-3xl font-bold">
              {content.why_different_title.value}
            </h3>
            <ul className="list-disc list-inside text-right text-lg space-y-2 mt-2">
              {content.why_different_points.value.map((item: any, index: number) => (
                <li key={index} className="transform-gpu">{item.point}</li>
              ))}
            </ul>
          </div>
          <div ref={whyImageRef} className="transform-gpu will-change-transform">
            <Image
              src={whyDifferentImage}
              width={500}
              height={500}
              alt="لماذا نحن مختلفون"
              className="hover:scale-105 transition-transform duration-500"
            />
          </div>
        </div>

        {/* Mission Section */}
        <div className="flex justify-between items-center gap-20 max-lg:gap-7 max-lg:flex-col mt-9">
          <div ref={missionImageRef} className="transform-gpu will-change-transform">
            <Image 
              src={missionImage} 
              width={500} 
              height={500} 
              alt="رسالتنا"
              className="hover:scale-105 transition-transform duration-500"
            />
          </div>
          <div ref={missionRef} className="transform-gpu">
            <h3 className="text-3xl font-bold">
              {content.mission_title.value}
            </h3>
            <div
              className="list-disc list-inside text-right text-lg mt-2"
              dangerouslySetInnerHTML={{
                __html: `<li>${content.mission_text.value}</li>`,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutPageClient;