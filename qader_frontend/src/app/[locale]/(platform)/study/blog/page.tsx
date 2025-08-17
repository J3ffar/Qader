"use client";

import { getBlogPosts, submitAdviceRequest } from "@/services/blog.service";
import { BlogPost } from "@/types/api/blog.types";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

const BlogCardSkeleton = () => (
  <div className="rounded-xl overflow-hidden shadow-sm animate-pulse bg-gray-200 dark:bg-gray-700 h-48 w-full" />
);
const BlogCard = ({ title, published_at, slug }: any) => (
  <Link href={`/study/blog/${slug}`}>
    <div className="rounded-xl overflow-hidden shadow-sm relative group">
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
  const [visibleCounts, setVisibleCounts] = useState<Record<string, number>>(
    {}
  );

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

  const groupedByTag: Record<string, BlogPost[]> =
    data?.results.reduce((acc, post) => {
      post.tags.forEach((tag: string) => {
        if (!acc[tag]) acc[tag] = [];
        acc[tag].push(post);
      });
      return acc;
    }, {} as Record<string, BlogPost[]>) ?? {};

  const handleToggle = (tag: string) => {
    setExpandedTags((prev) => ({ ...prev, [tag]: !prev[tag] }));
  };

  const handleSeeMore = (tag: string) => {
    setVisibleCounts((prev) => ({
      ...prev,
      [tag]: (prev[tag] || 20) + 10,
    }));
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
      {/* Categories section */}
      <div className="space-y-4">
        {!data ? (
          <div className=" grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mt-4">
            {Array.from({ length: 6 }).map((_, index) => (
              <BlogCardSkeleton key={index} />
            ))}
          </div>
        ) : (
          Object.entries(groupedByTag).map(([tag, posts]) => {
            const isExpanded = expandedTags[tag] ?? true;
            const visibleCount = visibleCounts[tag] ?? 20;

            return (
              <div
                key={tag}
                className="bg-white dark:bg-[#0B1739] p-4 rounded-xl shadow-sm"
              >
                <div
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => handleToggle(tag)}
                >
                  <h3 className="font-bold">{tag}</h3>
                  {isExpanded ? (
                    <ChevronUp size={20} />
                  ) : (
                    <ChevronDown size={20} />
                  )}
                </div>
                {isExpanded && (
                  <>
                    <div className=" flex flex-col sm:grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 mt-4">
                      {posts.slice(0, visibleCount).map((blog: any) => (
                        <BlogCard key={blog.id} {...blog} />
                      ))}
                    </div>
                    {posts.length > visibleCount && (
                      <div className="mt-4 text-center">
                        <button
                          onClick={() => handleSeeMore(tag)}
                          className="text-blue-600 underline text-sm"
                        >
                          عرض المزيد
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Support form section */}
      <div className="bg-white dark:bg-[#0B1739] p-6 rounded-xl shadow-sm flex flex-col lg:flex-row gap-6 ">
        <div className="lg:w-1/2">
          <h3 className="text-md font-bold mb-2">
            هل تواجه مشكلة؟!{" "}
            <Link href="/study/admin-support" className="text-[#074182]">
              اطلب نصيحة
            </Link>
          </h3>
          <p className="text-sm text-gray-600">
            - اكتب لنا المشكلة التي تواجه صعوبة فيها. <br />- سيتم الرد و{" "}
            <Link
              href="/study/admin-support"
              className="text-blue-600 underline"
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
              className="w-full border rounded-md p-2"
              value={problemType}
              onChange={(e) => setProblemType(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-sm font-bold mb-1">وصف المشكلة</label>
            <textarea
              rows={4}
              placeholder="اكتب وصف المشكلة..."
              className="w-full border rounded-md p-2"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <button
            type="submit"
            className="bg-[#074182] text-white px-4 py-2 rounded-md hover:bg-[#05356a] transition w-full"
            disabled={mutation.isPending}
          >
            {mutation.isPending ? "جاري الإرسال..." : " إرسال"}
          </button>
        </form>

        
      </div>
    </section>
  );
};

export default BlogSupportSection;
