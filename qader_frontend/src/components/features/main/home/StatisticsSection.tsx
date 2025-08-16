"use client";
import React, { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import type { Statistic } from "@/types/api/content.types";

// Register ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

type StatisticsProps = {
  data: Statistic[];
};

const StatisticsSection = ({ data }: StatisticsProps) => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const subtitleRef = useRef<HTMLParagraphElement>(null);
  const statsContainerRef = useRef<HTMLDivElement>(null);
  const statItemsRef = useRef<(HTMLDivElement | null)[]>([]);
  const valueRefs = useRef<(HTMLHeadingElement | null)[]>([]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set([titleRef.current, subtitleRef.current], {
        opacity: 0,
        y: 30,
      });

      gsap.set(statItemsRef.current, {
        opacity: 0,
        scale: 0.5,
        rotateX: -90,
      });

      // Create main timeline
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top 75%",
          end: "bottom 25%",
          toggleActions: "play none none reverse",
          onEnter: () => {
            // Trigger counter animations when section comes into view
            animateCounters();
          },
        },
      });

      // Animate title with typewriter effect
      tl.fromTo(
        titleRef.current,
        {
          opacity: 0,
          y: 30,
          clipPath: "polygon(0 0, 0 0, 0 100%, 0% 100%)",
        },
        {
          opacity: 1,
          y: 0,
          clipPath: "polygon(0 0, 100% 0, 100% 100%, 0 100%)",
          duration: 0.8,
          ease: "power3.out",
        }
      );

      // Animate subtitle
      tl.to(
        subtitleRef.current,
        {
          opacity: 1,
          y: 0,
          duration: 0.6,
          ease: "power2.out",
        },
        "-=0.4"
      );

      // Animate stat cards with 3D flip effect
      tl.to(
        statItemsRef.current,
        {
          opacity: 1,
          scale: 1,
          rotateX: 0,
          duration: 0.8,
          stagger: 0.15,
          ease: "back.out(1.5)",
          transformPerspective: 1000,
        },
        "-=0.3"
      );

      // Counter animation function
      const animateCounters = () => {
        valueRefs.current.forEach((valueRef, index) => {
          if (!valueRef || !data[index]) return;

          const stat = data[index];
          const value = stat.value;
          
          // Extract number from the value (handles formats like "1000+", "50K", etc.)
          const numMatch = value.match(/[\d,]+/);
          if (!numMatch) return;
          
          const numStr = numMatch[0].replace(/,/g, '');
          const targetNumber = parseInt(numStr);
          const suffix = value.replace(numMatch[0], '');
          
          // Animate the counter
          const counter = { value: 0 };
          gsap.to(counter, {
            value: targetNumber,
            duration: 2,
            delay: index * 0.1,
            ease: "power2.out",
            onUpdate: () => {
              const currentValue = Math.floor(counter.value);
              // Format with commas if original had them
              const formatted = value.includes(',') 
                ? currentValue.toLocaleString('en-US')
                : currentValue.toString();
              valueRef.textContent = formatted + suffix;
            },
          });
        });
      };

      // Add floating animation to stat cards
      statItemsRef.current.forEach((item, index) => {
        if (!item) return;

        gsap.to(item, {
          y: -5,
          duration: 2 + index * 0.2,
          repeat: -1,
          yoyo: true,
          ease: "sine.inOut",
          delay: 1 + index * 0.1,
        });
      });

      // Interactive hover effects
      statItemsRef.current.forEach((item, index) => {
        if (!item) return;

        const handleMouseEnter = () => {
          gsap.to(item, {
            scale: 1.05,
            rotateY: 5,
            boxShadow: "0 20px 40px rgba(7, 65, 130, 0.2)",
            duration: 0.3,
            ease: "power2.out",
            transformPerspective: 1000,
          });

          // Pulse effect on the value
          gsap.to(valueRefs.current[index], {
            scale: 1.1,
            color: "#e78b48",
            duration: 0.3,
            ease: "power2.out",
          });
        };

        const handleMouseLeave = () => {
          gsap.to(item, {
            scale: 1,
            rotateY: 0,
            boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
            duration: 0.3,
            ease: "power2.out",
          });

          gsap.to(valueRefs.current[index], {
            scale: 1,
            color: "",
            duration: 0.3,
            ease: "power2.out",
          });
        };

        item.addEventListener("mouseenter", handleMouseEnter);
        item.addEventListener("mouseleave", handleMouseLeave);

        // Cleanup
        return () => {
          item.removeEventListener("mouseenter", handleMouseEnter);
          item.removeEventListener("mouseleave", handleMouseLeave);
        };
      });

      // Parallax effect on scroll
      gsap.to(statsContainerRef.current, {
        yPercent: -5,
        ease: "none",
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top bottom",
          end: "bottom top",
          scrub: 1,
        },
      });

      // Add decorative animated elements
      const createFloatingShape = (className: string, delay: number) => {
        const shape = document.createElement("div");
        shape.className = className;
        sectionRef.current?.appendChild(shape);

        gsap.set(shape, {
          position: "absolute",
          width: "100px",
          height: "100px",
          borderRadius: "50%",
          background: "linear-gradient(135deg, #e78b48 0%, #074182 100%)",
          opacity: 0.05,
          left: `${Math.random() * 100}%`,
          top: `${Math.random() * 100}%`,
          zIndex: 0,
        });

        gsap.to(shape, {
          scale: 1.5,
          x: "random(-50, 50)",
          y: "random(-50, 50)",
          duration: "random(15, 20)",
          repeat: -1,
          yoyo: true,
          ease: "sine.inOut",
          delay: delay,
        });

        return shape;
      };

      // Create background shapes
      const shapes: HTMLDivElement[] = [];
      for (let i = 0; i < 3; i++) {
        shapes.push(createFloatingShape("floating-shape", i * 2));
      }

      // Add sparkle effect on achievement
      const addSparkle = () => {
        statItemsRef.current.forEach((item, index) => {
          if (!item) return;
          
          setTimeout(() => {
            const sparkle = document.createElement("div");
            sparkle.className = "sparkle";
            item.appendChild(sparkle);
            
            gsap.set(sparkle, {
              position: "absolute",
              width: "4px",
              height: "4px",
              backgroundColor: "#e78b48",
              borderRadius: "50%",
              left: "50%",
              top: "50%",
              xPercent: -50,
              yPercent: -50,
            });

            gsap.to(sparkle, {
              scale: 0,
              x: "random(-50, 50)",
              y: "random(-50, 50)",
              opacity: 0,
              duration: 1,
              ease: "power2.out",
              onComplete: () => sparkle.remove(),
            });

            gsap.fromTo(
              sparkle,
              { scale: 0, opacity: 1 },
              { scale: 3, opacity: 0, duration: 0.6, ease: "power2.out" }
            );
          }, 2000 + index * 200);
        });
      };

      // Trigger sparkle effect periodically
      const sparkleInterval = setInterval(addSparkle, 5000);

      // Cleanup
      return () => {
        shapes.forEach((shape) => shape.remove());
        clearInterval(sparkleInterval);
      };
    }, sectionRef);

    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, [data]);

  return (
    <div
      ref={sectionRef}
      className="bg-white dark:bg-[#081028] sm:px-0 px-4 relative overflow-hidden transform-gpu"
    >
      <div
        ref={statsContainerRef}
        className="flex flex-col justify-center items-center py-9 container mx-auto px-0 relative z-10"
      >
        <h2
          ref={titleRef}
          className="text-4xl font-bold mb-2 text-center transform-gpu"
          style={{
            textShadow: "0 2px 10px rgba(0,0,0,0.1)",
          }}
        >
          تعرف على إحصائياتنا
        </h2>
        <p
          ref={subtitleRef}
          className="text-xl mb-8 text-center dark:text-[#D9E1FA] transform-gpu"
        >
          أرقامنا تتحدث عن نجاحنا وثقة طلابنا.
        </p>
        <div className="flex justify-center items-center flex-wrap gap-4 w-full">
          {data.map((stat, index) => (
            <div
              key={index}
              ref={(el) => {
                statItemsRef.current[index] = el;
              }}
              className="py-5 px-2 rounded-lg text-2xl font-bold flex justify-center items-center flex-col border-2 bg-[#E7F1FE4D] border-[#cfe4fc] dark:bg-[#0B1739] dark:hover:bg-[#053061] shadow-md w-full max-w-[330px] grow cursor-pointer transform-gpu will-change-transform relative overflow-hidden group"
              style={{
                transformStyle: "preserve-3d",
                perspective: "1000px",
              }}
            >
              {/* Animated background gradient */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#e78b48]/0 via-[#074182]/5 to-[#e78b48]/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              {/* Animated border glow */}
              <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                <div className="absolute inset-[-2px] bg-gradient-to-r from-[#e78b48] via-[#074182] to-[#e78b48] rounded-lg blur-sm animate-pulse" />
              </div>
              
              <h3
                ref={(el) => {
                  valueRefs.current[index] = el;
                }}
                className="text-primary lg:text-4xl md:text-3xl text-2xl mb-1 relative z-10 transform-gpu font-mono"
              >
                {stat.value}
              </h3>
              <h3 className="text-foreground lg:text-3xl md:text-2xl text-xl relative z-10">
                {stat.label}
              </h3>
              
              {/* Corner accent */}
              <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-br from-[#e78b48]/20 to-transparent rounded-bl-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="absolute bottom-0 left-0 w-16 h-16 bg-gradient-to-tr from-[#074182]/20 to-transparent rounded-tr-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StatisticsSection;
