"use client";

import { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import type { Page } from "@/types/api/content.types";

// Register ScrollTrigger plugin
if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

const TermsAndConditionsClient = ({ content }: { content: Page<any> | null }) => {
  const [toc, setToc] = useState<{ id: string; title: string }[]>([]);
  const [activeSection, setActiveSection] = useState<string>("");
  
  // Refs for GSAP animations
  const containerRef = useRef<HTMLDivElement>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);
  const mainContentRef = useRef<HTMLDivElement>(null);
  const tocItemsRef = useRef<HTMLLIElement[]>([]);
  const tabsRef: any = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    if (!content?.content) return;

    const parser = new DOMParser();
    const doc = parser.parseFromString(content.content, "text/html");
    const headings = doc.querySelectorAll("h3[id]");
    const items = Array.from(headings).map((h) => ({
      id: h.id,
      title: h.textContent || "",
    }));
    setToc(items);

    // Set the first section as active by default
    if (items.length > 0) {
      setActiveSection(items[0].id);
    }

    // Initial GSAP animations
    const tl = gsap.timeline();
    
    // Container fade in
    tl.fromTo(containerRef.current, 
      { opacity: 0, y: 30 },
      { opacity: 1, y: 0, duration: 0.8, ease: "power2.out" }
    );

    // Sidebar slide in from left
    tl.fromTo(sidebarRef.current,
      { x: -100, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.6, ease: "back.out(1.7)" },
      "-=0.4"
    );

    // Main content slide in from right
    tl.fromTo(mainContentRef.current,
      { x: 100, opacity: 0 },
      { x: 0, opacity: 1, duration: 0.6, ease: "back.out(1.7)" },
      "-=0.5"
    );

    // Tabs animation
    tl.fromTo(tabsRef.current?.children,
      { y: -20, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.4, stagger: 0.1, ease: "power2.out" },
      "-=0.3"
    );

    // Title animation
    tl.fromTo(titleRef.current,
      { scale: 0.8, opacity: 0 },
      { scale: 1, opacity: 1, duration: 0.5, ease: "back.out(1.7)" },
      "-=0.2"
    );

    return () => {
      ScrollTrigger.getAll().forEach(trigger => trigger.kill());
    };
  }, [content]);

  useEffect(() => {
    if (toc.length === 0) return;

    // Animate TOC items when they're available
    gsap.fromTo(tocItemsRef.current,
      { x: 50, opacity: 0 },
      { 
        x: 0, 
        opacity: 1, 
        duration: 0.4, 
        stagger: 0.1, 
        ease: "power2.out",
        delay: 0.8
      }
    );

    // Setup ScrollTrigger for content headings
    setTimeout(() => {
      const headings = document.querySelectorAll("h3[id]");
      
      headings.forEach((heading) => {
        ScrollTrigger.create({
          trigger: heading,
          start: "top center",
          end: "bottom center",
          onEnter: () => setActiveSection(heading.id),
          onEnterBack: () => setActiveSection(heading.id),
        });

        // Animate headings on scroll
        gsap.fromTo(heading,
          { x: 50, opacity: 0 },
          {
            x: 0,
            opacity: 1,
            duration: 0.6,
            ease: "power2.out",
            scrollTrigger: {
              trigger: heading,
              start: "top 80%",
              once: true
            }
          }
        );
      });

      // Animate paragraphs
      const paragraphs = document.querySelectorAll("article p");
      paragraphs.forEach((p) => {
        gsap.fromTo(p,
          { y: 30, opacity: 0 },
          {
            y: 0,
            opacity: 1,
            duration: 0.5,
            ease: "power2.out",
            scrollTrigger: {
              trigger: p,
              start: "top 85%",
              once: true
            }
          }
        );
      });

      // Animate lists and other content
      const lists = document.querySelectorAll("article ul, article ol");
      lists.forEach((list) => {
        gsap.fromTo(list,
          { x: 30, opacity: 0 },
          {
            x: 0,
            opacity: 1,
            duration: 0.6,
            ease: "power2.out",
            scrollTrigger: {
              trigger: list,
              start: "top 85%",
              once: true
            }
          }
        );
      });

      // Scroll to first section on page load
      if (toc.length > 0) {
        setTimeout(() => {
          scrollToId(toc[0].id);
        }, 1000);
      }
    }, 500);

  }, [toc]);

  // Fixed scrollToId function using native browser API (like Code 1)
  const scrollToId = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      // Use native scrollIntoView for reliable scrolling
      element.scrollIntoView({ behavior: "smooth", block: "start" });
      setActiveSection(id);
    }
  };

  // GSAP hover animations for TOC items
  const handleTocHover = (e: React.MouseEvent, isEntering: boolean) => {
    const button = e.currentTarget;
    
    if (isEntering) {
      gsap.to(button, {
        x: -8,
        scale: 1.02,
        duration: 0.3,
        ease: "power2.out"
      });
      gsap.to(button.querySelector('.hover-bg'), {
        opacity: 1,
        duration: 0.3,
        ease: "power2.out"
      });
    } else {
      gsap.to(button, {
        x: 0,
        scale: 1,
        duration: 0.3,
        ease: "power2.out"
      });
      gsap.to(button.querySelector('.hover-bg'), {
        opacity: 0,
        duration: 0.3,
        ease: "power2.out"
      });
    }
  };

  // GSAP hover animation for sidebar card
  const handleCardHover = (e: React.MouseEvent, isEntering: boolean) => {
    const card = e.currentTarget;
    
    if (isEntering) {
      gsap.to(card, {
        scale: 1.03,
        y: -5,
        boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
        duration: 0.4,
        ease: "power2.out"
      });
    } else {
      gsap.to(card, {
        scale: 1,
        y: 0,
        boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
        duration: 0.4,
        ease: "power2.out"
      });
    }
  };

  // GSAP hover animation for main content
  const handleMainContentHover = (e: React.MouseEvent, isEntering: boolean) => {
    const main = e.currentTarget;
    
    if (isEntering) {
      gsap.to(main, {
        boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
        duration: 0.4,
        ease: "power2.out"
      });
    } else {
      gsap.to(main, {
        boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
        duration: 0.4,
        ease: "power2.out"
      });
    }
  };

  return (
    <div 
      ref={containerRef}
      className="flex flex-col md:flex-row p-4 md:p-10 gap-8 text-right dark:bg-[#081028]"
    >
      {/* Animated Sidebar */}
      <aside 
        ref={sidebarRef}
        className="md:w-1/3 lg:w-1/4 sticky top-24 self-start"
      >
        <div 
          className="bg-white dark:bg-[#0B1739] p-4 rounded-xl shadow-lg"
          onMouseEnter={(e) => handleCardHover(e, true)}
          onMouseLeave={(e) => handleCardHover(e, false)}
        >
          {/* Navigation Tabs */}
          <div ref={tabsRef} className="flex justify-around border-b border-gray-200 dark:border-gray-700 mb-4">
            <Link
              href="#"
              className="text-lg font-bold pb-2 px-2 text-[#074182] dark:text-[#3D93F5] border-b-2 border-[#074182] dark:border-[#3D93F5] relative"
            >
              الشروط والأحكام
              <span className="absolute bottom-0 left-0 w-full h-0.5 bg-[#074182] dark:bg-[#3D93F5]"></span>
            </Link>
            <Link
              href="/privacy"
              className="text-lg font-bold pb-2 px-2 text-gray-600 dark:text-gray-300 hover:text-black dark:hover:text-white transition-colors duration-300 relative group"
            >
              سياسة الخصوصية
              <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-gray-400 group-hover:w-full transition-all duration-300"></span>
            </Link>
          </div>

          {/* Table of Contents Header */}
          <p 
            ref={titleRef}
            className="text-lg font-bold text-gray-800 dark:text-gray-100 mb-4 text-center"
          >
            جدول المحتويات
          </p>

          {/* TOC Items */}
          <ul className="space-y-3 text-gray-700 dark:text-gray-300">
            {toc.map((item, index) => (
              <li 
                key={item.id}
                ref={(el) => {
                  if (el) tocItemsRef.current[index] = el;
                }}
              >
                <button
                  onClick={() => scrollToId(item.id)}
                  onMouseEnter={(e) => handleTocHover(e, true)}
                  onMouseLeave={(e) => handleTocHover(e, false)}
                  className={`text-right w-full p-2 rounded-lg relative overflow-hidden transition-colors duration-300 ${
                    activeSection === item.id 
                      ? 'text-[#2F80ED] bg-blue-50 dark:bg-blue-900/20 font-semibold' 
                      : 'hover:text-[#2F80ED]'
                  }`}
                >
                  {/* Hover background */}
                  <span 
                    className="hover-bg absolute inset-0 bg-gradient-to-r from-transparent to-blue-50 dark:to-blue-900/10 opacity-0 rounded-lg"
                  ></span>
                  
                  {/* Content */}
                  <span className="relative z-10">{item.title}</span>
                  
                  {/* Active indicator */}
                  {activeSection === item.id && (
                    <span className="absolute right-0 top-1/2 transform -translate-y-1/2 w-1 h-6 bg-[#2F80ED] rounded-full"></span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </aside>

      {/* Main Content */}
      <main 
        ref={mainContentRef}
        className="md:w-2/3 lg:w-3/4 bg-white dark:bg-[#0B1739] p-6 md:p-8 rounded-xl shadow-lg"
        onMouseEnter={(e) => handleMainContentHover(e, true)}
        onMouseLeave={(e) => handleMainContentHover(e, false)}
      >
        <article
          className="prose-lg dark:prose-invert max-w-none"
          dangerouslySetInnerHTML={{
            __html: content?.content || "<p>لا يتوفر محتوى حالياً.</p>",
          }}
        />
      </main>
    </div>
  );
};

export default TermsAndConditionsClient;
