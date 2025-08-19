"use client";

import { getBlogPosts, submitAdviceRequest } from "@/services/blog.service";
import { BlogPost } from "@/types/api/blog.types";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp } from "lucide-react";
import Link from "next/link";
import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import gsap from "gsap";

const BlogCardSkeleton = () => (
  <div className="rounded-xl overflow-hidden shadow-sm animate-pulse bg-gray-200 dark:bg-gray-700 h-48 w-full" />
);

const BlogCard = ({ title, published_at, slug }: any) => (
  <Link href={`/study/blog/${slug}`}>
    <div className="rounded-xl overflow-hidden shadow-sm relative group blog-card">
      <img
        src="/images/articles.jpg"
        alt={title}
        className="w-full h-48 object-cover"
      />
      <div
        className="absolute inset-0 bg-gradient-to-t from-[#074182cc] to-transparent p-4 flex flex-col justify-end text-white"
        style={{
          background:
            "linear-gradient(0deg, rgba(7, 65, 130, 0.8) 0%, rgba(7, 65, 130, 0) 100%)",
        }}
      >
        <h4 className="text-sm font-bold">{title}</h4>
        <p className="text-xs">
          {new Date(published_at).toLocaleDateString("ar-EG", {
            year: "numeric",
            month: "long",
            day: "numeric",
          })}
        </p>
      </div>
    </div>
  </Link>
);

const BlogSupportSection = () => {
  const [problemType, setProblemType] = useState("");
  const [description, setDescription] = useState("");
  const [expandedTags, setExpandedTags] = useState<Record<string, boolean>>({});
  const [visibleCounts, setVisibleCounts] = useState<Record<string, number>>({});
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<"articles" | "strategies">("articles");
  
  const contentRef = useRef<HTMLDivElement>(null);
  const articlesRef = useRef<HTMLDivElement>(null);
  const strategiesRef = useRef<HTMLDivElement>(null);
  const switcherRef = useRef<HTMLDivElement>(null);

  const { data } = useQuery({
    queryKey: ["blogPosts"],
    queryFn: () => getBlogPosts({ page_size: 100 }),
  });

  const mutation = useMutation({
    mutationFn: submitAdviceRequest,
    onSuccess: () => {
      toast.success("تم إرسال الطلب بنجاح");
      setProblemType("");
      setDescription("");
    },
    onError: () => {
      toast.error("حدث خطأ أثناء الإرسال، حاول مرة أخرى");
    },
  });

  // Filter results based on search
  const filteredResults = data?.results?.filter((post: BlogPost) => {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    return (
      post.title.toLowerCase().includes(searchLower) ||
      post.tags.some((tag: string) => tag.toLowerCase().includes(searchLower))
    );
  }) ?? [];

  // Separate blogs into two categories
  const articleBlogs = filteredResults.filter((post: BlogPost) => 
    post.tags.includes("مقالات تعليمية")
  );
  
  const strategyBlogs = filteredResults.filter((post: BlogPost) => 
    post.tags.includes("استراتيجيات الحل الذكية")
  );

  // Group by tag for the selected category
  const currentCategoryBlogs = selectedCategory === "articles" ? articleBlogs : strategyBlogs;
  
  const groupedByTag: Record<string, BlogPost[]> =
    currentCategoryBlogs.reduce((acc, post) => {
      post.tags.forEach((tag: string) => {
        if (!acc[tag]) acc[tag] = [];
        acc[tag].push(post);
      });
      return acc;
    }, {} as Record<string, BlogPost[]>) ?? {};

  // GSAP Animations
  useEffect(() => {
    if (!switcherRef.current) return;
    
    // Animate switcher indicator
    const indicator = switcherRef.current.querySelector('.switcher-indicator');
    if (indicator) {
      gsap.to(indicator, {
        x: selectedCategory === "articles" ? "100%" : 0,
        duration: 0.3,
        ease: "power2.inOut"
      });
    }
  }, [selectedCategory]);

  useEffect(() => {
    if (!contentRef.current) return;

    const tl = gsap.timeline();
    
    // Fade out current content
    tl.to(contentRef.current, {
      opacity: 0,
      y: 20,
      duration: 0.2,
      ease: "power2.in",
      onComplete: () => {
        // Content will be swapped by React
      }
    })
    // Fade in new content
    .to(contentRef.current, {
      opacity: 1,
      y: 0,
      duration: 0.3,
      ease: "power2.out"
    });

    // Animate blog cards on category change
    const cards = contentRef.current.querySelectorAll('.blog-card');
    gsap.fromTo(cards, 
      {
        opacity: 0,
        y: 30,
        scale: 0.95
      },
      {
        opacity: 1,
        y: 0,
        scale: 1,
        duration: 0.4,
        stagger: 0.05,
        ease: "power2.out",
        delay: 0.2
      }
    );
  }, [selectedCategory, currentCategoryBlogs]);

  const handleToggle = (tag: string) => {
    setExpandedTags((prev) => ({ ...prev, [tag]: !prev[tag] }));
    
    // Animate the expansion
    const tagSection = document.querySelector(`[data-tag="${tag}"]`);
    if (tagSection) {
      const content = tagSection.querySelector('.tag-content');
      if (content) {
        if (expandedTags[tag]) {
          gsap.to(content, {
            height: 0,
            opacity: 0,
            duration: 0.3,
            ease: "power2.inOut"
          });
        } else {
          gsap.fromTo(content, 
            {
              height: 0,
              opacity: 0
            },
            {
              height: "auto",
              opacity: 1,
              duration: 0.3,
              ease: "power2.inOut"
            }
          );
        }
      }
    }
  };

  const handleSeeMore = (tag: string) => {
    setVisibleCounts((prev) => ({
      ...prev,
      [tag]: (prev[tag] || 20) + 10,
    }));
  };

  const handleCategorySwitch = (category: "articles" | "strategies") => {
    if (category === selectedCategory) return;
    setSelectedCategory(category);
    setExpandedTags({}); // Reset expanded state when switching
    setVisibleCounts({}); // Reset visible counts
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!problemType && !description) {
      toast.error("يرجى كتابة نوع المشكلة ووصفها");
      return;
    }
    if (!problemType) {
      toast.error("يرجى كتابة نوع المشكلة");
      return;
    }
    if (!description) {
      toast.error("يرجى كتابة وصف المشكلة");
      return;
    }

    mutation.mutate({ problem_type: problemType, description });
  };

  return (
    <section className="container mx-auto p-4 space-y-6 max-w-screen-xl">
      {/* Search Bar */}
      <div className="mb-4 flex justify-center">
        <input
          type="text"
          placeholder="ابحث عن مقال أو كلمة مفتاحية..."
          className="w-full max-w-md border rounded-md p-2 shadow-sm"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      {/* Category Switcher */}
      <div className="flex justify-center mb-6">
        <div 
          ref={switcherRef}
          className="relative bg-gray-100 dark:bg-gray-800 rounded-full p-1 flex gap-4"
        >
          {/* Animated Background Indicator */}
          <div 
            className="switcher-indicator absolute top-1 left-1 w-[calc(50%-4px)] h-[calc(100%-8px)] bg-[#074182] rounded-full shadow-lg"
            style={{ transition: 'none' }}
          />
          
          {/* Buttons */}
          <button
            onClick={() => handleCategorySwitch("articles")}
            className={`relative z-10 px-6 flex justify-center py-2 rounded-full font-semibold transition-colors duration-300 ${
              selectedCategory === "articles" 
                ? "text-white dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
                : "text-gray-600" 
            }`}
          >
            مقالات تعليمية
          </button>
          
          <button
            onClick={() => handleCategorySwitch("strategies")}
            className={`relative z-10 px-6 flex justify-center py-2 rounded-full font-semibold transition-colors duration-300 ${
              selectedCategory === "strategies" 
               ? "text-white dark:text-gray-300 hover:text-gray-800 dark:hover:text-white"
                : "text-gray-600" 
            }`}
          >
            استراتيجيات الحل الذكية
          </button>
        </div>
      </div>

      {/* Categories section */}
      <div ref={contentRef} className="space-y-4">
        {!data ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mt-4">
            {Array.from({ length: 6 }).map((_, index) => (
              <BlogCardSkeleton key={index} />
            ))}
          </div>
        ) : (
          Object.keys(groupedByTag).length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              لا توجد نتائج مطابقة للبحث في {selectedCategory === "articles" ? "المقالات التعليمية" : "استراتيجيات الحل الذكية"}.
            </div>
          ) : (
            Object.entries(groupedByTag).map(([tag, posts]) => {
              const isExpanded = expandedTags[tag] ?? true;
              const visibleCount = visibleCounts[tag] ?? 20;
              
              // Skip rendering the main category tag as a separate section
              if (tag === "مقالات تعليمية" || tag === "استراتيجيات الحل الذكية") {
                return (
                  <div key={tag} className="flex flex-col sm:grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {posts.slice(0, visibleCount).map((blog: any) => (
                      <BlogCard key={blog.id} {...blog} />
                    ))}
                    {posts.length > visibleCount && (
                      <div className="col-span-full mt-4 text-center">
                        <button
                          onClick={() => handleSeeMore(tag)}
                          className="text-blue-600 underline text-sm hover:text-blue-700 transition-colors"
                        >
                          عرض المزيد
                        </button>
                      </div>
                    )}
                  </div>
                );
              }
              
              return (
                <div
                  key={tag}
                  data-tag={tag}
                  className="bg-white dark:bg-[#0B1739] p-4 rounded-xl shadow-sm"
                >
                  <div
                    className="flex items-center justify-between cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 -m-4 p-4 rounded-t-xl transition-colors"
                    onClick={() => handleToggle(tag)}
                  >
                    <h3 className="font-bold">{tag}</h3>
                    <div className="transition-transform duration-300" style={{
                      transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)'
                    }}>
                      <ChevronDown size={20} />
                    </div>
                  </div>
                  {isExpanded && (
                    <div className="tag-content">
                      <div className="flex flex-col sm:grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mt-4">
                        {posts.slice(0, visibleCount).map((blog: any) => (
                          <BlogCard key={blog.id} {...blog} />
                        ))}
                      </div>
                      {posts.length > visibleCount && (
                        <div className="mt-4 text-center">
                          <button
                            onClick={() => handleSeeMore(tag)}
                            className="text-blue-600 underline text-sm hover:text-blue-700 transition-colors"
                          >
                            عرض المزيد
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )
        )}
      </div>

      {/* Support form section */}
      <div className="bg-white dark:bg-[#0B1739] p-6 rounded-xl shadow-sm flex flex-col lg:flex-row gap-6">
        <div className="lg:w-1/2">
          <h3 className="text-md font-bold mb-2">
            هل تواجه مشكلة؟!{" "}
            <Link href="/study/admin-support" className="text-[#074182] hover:text-[#05356a] transition-colors">
              اطلب نصيحة
            </Link>
          </h3>
          <p className="text-sm text-gray-600">
            - اكتب لنا المشكلة التي تواجه صعوبة فيها. <br />- سيتم الرد و{" "}
            <Link
              href="/study/admin-support"
              className="text-blue-600 underline hover:text-blue-700 transition-colors"
            >
              الدعم الخارجي
            </Link>{" "}
            يمكنه خدمتك لاحقاً بدون ذكر اسمك.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="flex-1 space-y-4 rounded-[10px] p-[10px] shadow-md dark:shadow-[1px_5px_30px_#052c5c]"
        >
          <div>
            <label className="block text-sm font-bold mb-1">نوع المشكلة</label>
            <input
              type="text"
              placeholder="صعوبة في المذاكرة"
              className="w-full border rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-[#074182] transition-all"
              value={problemType}
              onChange={(e) => setProblemType(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-bold mb-1">وصف المشكلة</label>
            <textarea
              rows={4}
              placeholder="اكتب وصف المشكلة..."
              className="w-full border rounded-md p-2 focus:outline-none focus:ring-2 focus:ring-[#074182] transition-all resize-none"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <button
            type="submit"
            className="bg-[#074182] text-white px-4 py-2 rounded-md hover:bg-[#05356a] transition-all w-full transform hover:scale-[1.02] active:scale-[0.98]"
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "جاري الإرسال..." : "إرسال"}
          </button>
        </form>
      </div>
    </section>
  );
};

export default BlogSupportSection;
