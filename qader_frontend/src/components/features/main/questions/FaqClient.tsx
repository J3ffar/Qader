"use client";

import React, { useState, useMemo, useEffect, useRef } from "react";
import {
  ChevronDownIcon,
  MagnifyingGlassIcon,
  PaperAirplaneIcon,
} from "@heroicons/react/24/solid";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import type { FaqPageData } from "@/types/api/content.types";
import Link from "next/link";

// Register ScrollTrigger plugin
gsap.registerPlugin(ScrollTrigger);

interface FaqClientProps {
  data: FaqPageData | null;
}

const FaqClient: React.FC<FaqClientProps> = ({ data }) => {
  const [activeCategoryName, setActiveCategoryName] = useState<string>(
    data?.faq_data?.[0]?.name ?? ""
  );
  const [activeItem, setActiveItem] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState("");

  // Refs for animations
  const pageRef = useRef<HTMLDivElement>(null);
  const heroRef = useRef<HTMLDivElement>(null);
  const searchBarRef = useRef<HTMLDivElement>(null);
  const categoriesRef = useRef<HTMLDivElement>(null);
  const categoryButtonsRef = useRef<(HTMLButtonElement | null)[]>([]);
  const questionsRef = useRef<HTMLDivElement>(null);
  const ctaRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const pageContent = data?.page_content?.content_structured_resolved;
  const heroTitle = pageContent?.hero_title.value ?? "الأسئلة الشائعة";
  const heroSubtitle =
    pageContent?.hero_subtitle.value ?? "لديك سؤال؟ لدينا الإجابة.";
  const ctaTitle = pageContent?.cta_title.value ?? "هل ما زلت تحتاج مساعدة؟";
  const ctaButtonText = pageContent?.cta_button_text.value ?? "تواصل معنا";

  // Memoize the filtered data to avoid re-calculating on every render
  const filteredFaqData = useMemo(() => {
    if (!data?.faq_data) return [];
    if (!searchTerm.trim()) return data.faq_data;

    const lowercasedFilter = searchTerm.toLowerCase();

    return data.faq_data
      .map((category) => ({
        ...category,
        items: category.items.filter(
          (item) =>
            item.question.toLowerCase().includes(lowercasedFilter) ||
            item.answer.toLowerCase().includes(lowercasedFilter)
        ),
      }))
      .filter((category) => category.items.length > 0);
  }, [searchTerm, data]);

  // Effect to reset active category if it's no longer in the filtered list
  React.useEffect(() => {
    if (
      filteredFaqData.length > 0 &&
      !filteredFaqData.some((c) => c.name === activeCategoryName)
    ) {
      setActiveCategoryName(filteredFaqData[0].name);
    } else if (filteredFaqData.length === 0) {
      setActiveCategoryName("");
    }
  }, [filteredFaqData, activeCategoryName]);

  // GSAP Animations
  useEffect(() => {
    const ctx = gsap.context(() => {
      // Set initial states
      gsap.set([heroRef.current, searchBarRef.current], {
        opacity: 0,
        y: 30,
      });

      gsap.set(categoriesRef.current, {
        opacity: 0,
        y: 30,
      });

      gsap.set(categoryButtonsRef.current, {
        opacity: 0,
        scale: 0.8,
      });

      gsap.set(questionsRef.current, {
        opacity: 0,
        y: 20,
      });

      gsap.set(ctaRef.current, {
        opacity: 0,
        y: 40,
      });

      // Create timeline for entrance animations
      const tl = gsap.timeline({
        defaults: { ease: "power3.out" }
      });

      // Animate hero section
      tl.to(heroRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.8,
      });

      // Animate search bar with bounce
      tl.to(searchBarRef.current, {
        opacity: 1,
        y: 0,
        duration: 0.6,
        ease: "back.out(1.2)",
      }, "-=0.4");

      // Animate categories section when it enters viewport
      ScrollTrigger.create({
        trigger: categoriesRef.current,
        start: "top bottom", // Trigger when top of element reaches bottom of viewport
        onEnter: () => {
          // First animate the categories container
          gsap.to(categoriesRef.current, {
            opacity: 1,
            y: 0,
            duration: 0.6,
            ease: "power2.out",
            onComplete: () => {
              // Then animate category buttons with stagger - they must appear first
              gsap.to(categoryButtonsRef.current, {
                opacity: 1,
                scale: 1,
                duration: 0.5,
                stagger: 0.12, // Increased stagger for more visible sequential appearance
                ease: "back.out(1.5)",
                onComplete: () => {
                  // Add a delay before questions appear to ensure buttons are fully visible
                  gsap.delayedCall(0.3, () => {
                    // Finally animate questions after categories are completely visible
                    gsap.to(questionsRef.current, {
                      opacity: 1,
                      y: 0,
                      duration: 0.6,
                      ease: "power2.out",
                      onComplete: () => {
                        // Animate individual question items with more noticeable stagger
                        const questions = questionsRef.current?.querySelectorAll('.question-item');
                        if (questions) {
                          gsap.fromTo(questions,
                            { opacity: 0, x: -20 },
                            { 
                              opacity: 1, 
                              x: 0, 
                              duration: 0.4,
                              stagger: 0.08, // Increased stagger for better visibility
                              ease: "power2.out"
                            }
                          );
                        }
                      }
                    });
                  });
                }
              });
            }
          });
        },
        toggleActions: "play none none reverse"
      });

      // Animate CTA section on scroll
      ScrollTrigger.create({
        trigger: ctaRef.current,
        start: "top bottom", // Changed from "top 85%" to "top bottom"
        onEnter: () => {
          gsap.to(ctaRef.current, {
            opacity: 1,
            y: 0,
            duration: 0.8,
            ease: "power2.out",
          });
        },
        toggleActions: "play none none reverse"
      });

      // Add floating animation to search bar
      gsap.to(searchBarRef.current, {
        y: -5,
        duration: 2.5,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        delay: 1.5,
      });

      // Search bar focus animation
      const searchInput = searchBarRef.current?.querySelector('input');
      if (searchInput) {
        searchInput.addEventListener('focus', () => {
          gsap.to(searchBarRef.current, {
            scale: 1.02,
            boxShadow: "0 10px 30px rgba(7, 65, 130, 0.2)",
            duration: 0.3,
            ease: "power2.out",
          });
        });

        searchInput.addEventListener('blur', () => {
          gsap.to(searchBarRef.current, {
            scale: 1,
            boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
            duration: 0.3,
            ease: "power2.out",
          });
        });
      }

      // Category button hover animations
      categoryButtonsRef.current.forEach((button) => {
        if (!button) return;

        button.addEventListener('mouseenter', () => {
          if (button.classList.contains('active')) return;
          gsap.to(button, {
            scale: 1.05,
            duration: 0.2,
            ease: "power2.out",
          });
        });

        button.addEventListener('mouseleave', () => {
          if (button.classList.contains('active')) return;
          gsap.to(button, {
            scale: 1,
            duration: 0.2,
            ease: "power2.out",
          });
        });
      });

      // Button hover animation
      if (buttonRef.current) {
        buttonRef.current.addEventListener('mouseenter', () => {
          gsap.to(buttonRef.current, {
            scale: 1.05,
            duration: 0.2,
            ease: "power2.out",
          });
          
          const icon = buttonRef.current?.querySelector('.airplane-icon');
          if (icon) {
            gsap.to(icon, {
              x: 3,
              y: -3,
              duration: 0.3,
              ease: "power2.out",
            });
          }
        });

        buttonRef.current.addEventListener('mouseleave', () => {
          gsap.to(buttonRef.current, {
            scale: 1,
            duration: 0.2,
            ease: "power2.out",
          });
          
          const icon = buttonRef.current?.querySelector('.airplane-icon');
          if (icon) {
            gsap.to(icon, {
              x: 0,
              y: 0,
              duration: 0.3,
              ease: "power2.out",
            });
          }
        });
      }

      // Add decorative floating particles
      const createParticle = () => {
        const particle = document.createElement('div');
        particle.className = 'faq-particle';
        pageRef.current?.appendChild(particle);
        
        const startX = Math.random() * window.innerWidth;
        
        gsap.set(particle, {
          position: 'fixed',
          width: '3px',
          height: '3px',
          backgroundColor: '#074182',
          borderRadius: '50%',
          left: startX,
          bottom: -10,
          opacity: 0.2,
          zIndex: 0,
        });

        gsap.to(particle, {
          y: -window.innerHeight - 100,
          x: `random(-50, 50)`,
          opacity: 0,
          duration: `random(10, 15)`,
          ease: "none",
          onComplete: () => particle.remove(),
        });
      };

      // Create particles periodically
      const particleInterval = setInterval(createParticle, 3000);

      return () => {
        clearInterval(particleInterval);
      };
    }, pageRef);

    return () => {
      ctx.revert();
      ScrollTrigger.getAll().forEach((trigger) => trigger.kill());
    };
  }, []);

  // Animate questions when category changes
  const handleCategoryChange = (categoryName: string) => {
    setActiveCategoryName(categoryName);
    setActiveItem(null);
    
    // Animate questions appearing
    if (questionsRef.current) {
      gsap.fromTo(questionsRef.current,
        { opacity: 0, y: 20 },
        { 
          opacity: 1, 
          y: 0, 
          duration: 0.5, 
          ease: "power2.out",
          onComplete: () => {
            const questions = questionsRef.current?.querySelectorAll('.question-item');
            if (questions) {
              gsap.fromTo(questions,
                { opacity: 0, x: -20 },
                { 
                  opacity: 1, 
                  x: 0, 
                  duration: 0.3,
                  stagger: 0.05,
                  ease: "power2.out"
                }
              );
            }
          }
        }
      );
    }
  };

  // Animate answer expansion
  const handleQuestionToggle = (itemId: number) => {
    const isOpening = activeItem !== itemId;
    setActiveItem(isOpening ? itemId : null);

    if (isOpening) {
      setTimeout(() => {
        const answerElement = document.getElementById(`answer-${itemId}`);
        if (answerElement) {
          gsap.fromTo(answerElement,
            { 
              opacity: 0, 
              height: 0,
              y: -10 
            },
            { 
              opacity: 1, 
              height: "auto",
              y: 0, 
              duration: 0.4, 
              ease: "power2.out" 
            }
          );
        }
      }, 0);
    }
  };

  return (
    <div ref={pageRef} className="bg-white dark:bg-[#081028] sm:px-0 px-3 py-10 min-h-screen overflow-hidden transform-gpu">
      <div className="flex justify-center items-center gap-6 flex-col container mx-auto">
        <div ref={heroRef} className="text-center px-4 transform-gpu">
          <h2 className="text-4xl font-bold" style={{ textShadow: "0 2px 10px rgba(0,0,0,0.1)" }}>
            {heroTitle}
          </h2>
          <p className="text-gray-800 text-lg dark:text-[#D9E1FA] mt-2">
            {heroSubtitle}
          </p>
        </div>

        {/* Search Bar */}
        <div ref={searchBarRef} className="relative w-full max-w-lg shadow-md rounded-lg transform-gpu">
          <input
            type="text"
            placeholder="اكتب كلمة للبحث في الأسئلة والأجوبة..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full border border-gray-300 dark:border-gray-600 dark:bg-gray-800 rounded-lg py-3 pr-10 pl-4 focus:outline-none focus:ring-2 focus:ring-[#074182] transition-all duration-300"
          />
          <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute right-4 top-1/2 -translate-y-1/2" />
        </div>

        {/* Categories Navbar */}
        <div ref={categoriesRef} className="p-4 md:p-10 w-full transform-gpu">
          <div className="flex gap-4 justify-center text-center border-b border-gray-200 dark:border-gray-700 flex-wrap">
            {filteredFaqData.map((category, index) => (
              <button
                key={category.id}
                ref={(el) => { categoryButtonsRef.current[index] = el; }}
                onClick={() => handleCategoryChange(category.name)}
                className={`py-2 px-4 font-semibold rounded-t-md transition-all border-b-2 transform-gpu ${
                  activeCategoryName === category.name
                    ? "text-[#074182] border-[#074182] active"
                    : "text-gray-600 dark:text-gray-300 border-transparent hover:text-[#074182] hover:border-gray-300"
                }`}
              >
                {category.name}
              </button>
            ))}
          </div>

          {/* Questions List */}
          <div ref={questionsRef} className="mt-4 space-y-2 transform-gpu">
            {filteredFaqData
              .find((c) => c.name === activeCategoryName)
              ?.items.map((item, index) => (
                <div
                  key={item.id}
                  className="question-item border-b border-gray-200 dark:border-gray-700 transform-gpu"
                >
                  <button
                    onClick={() => handleQuestionToggle(item.id)}
                    className="w-full flex items-center justify-between text-right font-medium py-4 hover:bg-gray-50 dark:hover:bg-gray-800 px-2 rounded-lg transition-colors duration-200 group"
                  >
                    <span className="font-bold text-lg group-hover:text-[#074182] transition-colors duration-200">
                      {item.question}
                    </span>
                    <ChevronDownIcon
                      className={`w-5 h-5 text-gray-500 transition-transform duration-300 ${
                        activeItem === item.id ? "rotate-180 text-[#074182]" : ""
                      }`}
                    />
                  </button>
                  {activeItem === item.id && (
                    <div 
                      id={`answer-${item.id}`}
                      className="pb-4 pr-2 text-gray-700 dark:text-gray-300 leading-relaxed"
                    >
                      <p>{item.answer}</p>
                    </div>
                  )}
                </div>
              ))}
            {filteredFaqData.length > 0 &&
              !filteredFaqData.find((c) => c.name === activeCategoryName) && (
                <p className="text-center text-gray-500 py-10">
                  الرجاء اختيار تصنيف لعرض الأسئلة.
                </p>
              )}
            {filteredFaqData.length === 0 && searchTerm && (
              <p className="text-center text-gray-500 py-10">
                لا توجد نتائج بحث تطابق '{searchTerm}'
              </p>
            )}
          </div>
        </div>

        {/* Contact Prompt */}
        <div ref={ctaRef} className="text-center flex flex-col justify-center items-center pb-9 transform-gpu">
          <h2 className="text-4xl font-bold">{ctaTitle}</h2>
          <Link href="/contact" passHref>
            <button 
              ref={buttonRef}
              className="mt-4 flex items-center justify-center gap-2 py-3 px-8 rounded-lg bg-[#074182] text-white font-semibold hover:bg-[#053061] transition-all transform-gpu relative overflow-hidden group"
            >
              <span className="relative z-10">{ctaButtonText}</span>
              <PaperAirplaneIcon className="airplane-icon w-5 h-5 relative z-10 transform-gpu" />
              
              {/* Button shine effect */}
              <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-700 ease-out" />
            </button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default FaqClient;
