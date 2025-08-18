"use client";
import React, { useEffect, useRef } from "react";
import { User } from "lucide-react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import type { HomepageData, Review } from "@/types/api/content.types";

// Register ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

type ReviewProps = {
  data: HomepageData["praise"];
};

const ReviewCard = ({ review, index }: { review: Review; index: number }) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const iconRef = useRef<HTMLDivElement>(null);
  const quoteRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial state
      gsap.set(cardRef.current, {
        opacity: 0,
        y: 50,
        rotateX: -15,
      });

      // Scroll-triggered animation
      gsap.to(cardRef.current, {
        opacity: 1,
        y: 0,
        rotateX: 0,
        duration: 0.8,
        delay: index * 0.15, // Stagger effect
        ease: "power3.out",
        scrollTrigger: {
          trigger: cardRef.current,
          start: "top 120%",
          end: "bottom 15%",
          toggleActions: "play none none reverse",
        }
      });

      // Icon pulse animation
      gsap.to(iconRef.current, {
        scale: 1.1,
        duration: 1.5,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 1 + index * 0.2
      });

      // Quote marks animation
      const quoteTl = gsap.timeline({ repeat: -1, repeatDelay: 5 });
      quoteTl.fromTo(quoteRef.current,
        { 
          backgroundImage: "linear-gradient(90deg, #e78b48 0%, #074182 50%, #e78b48 100%)",
          backgroundSize: "200% auto",
          backgroundPosition: "0% center",
          backgroundClip: "text",
          WebkitBackgroundClip: "text",
          color: "transparent"
        },
        {
          backgroundPosition: "200% center",
          duration: 3,
          ease: "power1.inOut"
        }
      );

    }, cardRef);

    // Mouse move parallax effect
    const handleMouseMove = (e: MouseEvent) => {
      if (!cardRef.current) return;
      
      const rect = cardRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      
      gsap.to(cardRef.current, {
        rotateY: x * 0.05,
        rotateX: -y * 0.05,
        duration: 0.5,
        ease: "power2.out",
        transformPerspective: 1000
      });
    };

    const handleMouseLeave = () => {
      gsap.to(cardRef.current, {
        rotateY: 0,
        rotateX: 0,
        duration: 0.5,
        ease: "power2.out"
      });
    };

    const cardElement = cardRef.current;
    if (cardElement) {
      cardElement.addEventListener("mousemove", handleMouseMove);
      cardElement.addEventListener("mouseleave", handleMouseLeave);
    }

    return () => {
      ctx.revert();
      if (cardElement) {
        cardElement.removeEventListener("mousemove", handleMouseMove);
        cardElement.removeEventListener("mouseleave", handleMouseLeave);
      }
    };
  }, [index]);

  return (
    <div
      ref={cardRef}
      className={`w-full shadow-xl rounded-2xl flex flex-col justify-start items-center text-center border-r-8 p-6 sm:p-8 border-r-[#e78b48] transition-all delay-150 duration-300 ease-in-out hover:bg-[#E7F1FE4D] dark:hover:bg-[#053061] hover:border-r-[#074182] hover:shadow-2xl bg-card text-card-foreground transform-gpu will-change-transform relative overflow-hidden`}
      style={{ transformStyle: "preserve-3d" }}
    >
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-[#e78b48]/5 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-500" />
      
      <div 
        ref={iconRef}
        className="w-14 h-14 mb-4 flex justify-center items-center rounded-full bg-[#EDEDED] relative z-10 transform-gpu"
      >
        <User className="w-6 h-6 text-muted-foreground" />
      </div>
      <h3 className="font-bold text-lg relative z-10">{review.name}</h3>
      <p className="text-sm text-muted-foreground mb-3 relative z-10">{review.title}</p>
      <p ref={quoteRef} className="text-base relative z-10 font-medium">
        "{review.quote}"
      </p>
      
      {/* Shine effect on hover */}
      <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -skew-x-12 translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-1000 ease-out" />
    </div>
  );
};

const ReviewSection = ({ data }: ReviewProps) => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const title =
    data?.content_structured_resolved?.section_title?.value ??
    "ماذا قالوا <span class='text-[#074182] dark:text-[#3D93F5]'>عنا؟</span>";
  const subtitle =
    data?.content_structured_resolved?.section_subtitle?.value ??
    "آراء طلابنا هي شهادة نجاحنا.";
  const reviews = data?.content_structured_resolved?.reviews?.value ?? [];

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set([titleRef.current, subtitleRef.current], {
        opacity: 0,
        y: 30
      });

      // Create timeline for header animations
      const headerTl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 120%",
          end: "bottom 20%",
          toggleActions: "play none none reverse",
        }
      });

      // Animate title with split text effect
      headerTl.to(titleRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.8,
        ease: "power3.out"
      });

      // Animate subtitle
      headerTl.to(subtitleRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.6,
        ease: "power2.out"
      }, "-=0.4");

      // Add floating animation to the entire section
      gsap.to(containerRef.current, {
        y: -5,
        duration: 3,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      });

      // Parallax effect on scroll
      gsap.to(sectionRef.current, {
        yPercent: -5,
        ease: "none",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top bottom",
          end: "bottom top",
          scrub: 1
        }
      });

      // Add decorative floating elements
      const createFloatingElement = (delay: number) => {
        const element = document.createElement('div');
        element.className = 'absolute w-2 h-2 bg-[#e78b48]/20 rounded-full pointer-events-none';
        element.style.left = `${Math.random() * 100}%`;
        element.style.top = `${Math.random() * 100}%`;
        sectionRef.current?.appendChild(element);

        gsap.to(element, {
          y: -30,
          x: "random(-30, 30)",
          opacity: 0,
          duration: "random(2, 4)",
          repeat: -1,
          delay: delay,
          ease: "power1.out"
        });

        return element;
      };

      // Create multiple floating elements
      const floatingElements: HTMLDivElement[] = [];
      for (let i = 0; i < 10; i++) {
        floatingElements.push(createFloatingElement(i * 0.1));
      }

      // Cleanup floating elements
      return () => {
        floatingElements.forEach(el => el.remove());
      };

    }, sectionRef);

    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    };
  }, []);

  return (
    <div 
      ref={sectionRef}
      className="bg-[#F9F9FA] dark:bg-[#0B1739] md:px-20 container mx-auto relative overflow-hidden transform-gpu"
    >
      <div 
        ref={containerRef}
        className="py-6 sm:py-8 md:py-10 relative"
      >
        <div className="mb-8 text-center sm:text-right">
          <h2
            ref={titleRef}
            className="text-4xl font-bold mb-2 transform-gpu"
            dangerouslySetInnerHTML={{ __html: title }}
            style={{
              textShadow: "0 2px 10px rgba(0,0,0,0.1)"
            }}
          />
          <p 
            ref={subtitleRef}
            className="text-lg text-muted-foreground dark:text-[#D9E1FA] transform-gpu"
          >
            {subtitle}
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8">
          {reviews.map((review, index) => (
            <ReviewCard key={index} review={review} index={index} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ReviewSection;
