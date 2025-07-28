"use client";

import { getBlogPostBySlug } from "@/services/blog.service";
import { useQuery } from "@tanstack/react-query";
import { Facebook, Instagram, Linkedin, Twitter } from "lucide-react";

import Image from "next/image";
import { useParams } from "next/navigation";
const ArticleSkeleton = () => (
  <div className="max-w-3xl mx-auto p-4 space-y-10 animate-pulse">
    <div className="w-full h-64 rounded-lg bg-gray-300 dark:bg-gray-700" />

    <div className="space-y-2">
      <div className="h-6 w-3/4 bg-gray-300 dark:bg-gray-700 rounded"></div>
      <div className="h-4 w-1/2 bg-gray-300 dark:bg-gray-700 rounded"></div>
    </div>

    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="h-4 w-full bg-gray-300 dark:bg-gray-700 rounded"
        />
      ))}
      <div className="h-4 w-2/3 bg-gray-300 dark:bg-gray-700 rounded" />
    </div>

    <div className="bg-gray-100 dark:bg-[#081028] text-center p-6 rounded-xl space-y-3">
      <div className="w-16 h-16 bg-gray-300 dark:bg-gray-600 rounded-full mx-auto" />
      <div className="h-4 w-1/3 bg-gray-300 dark:bg-gray-600 rounded mx-auto" />
      <div className="h-3 w-1/2 bg-gray-300 dark:bg-gray-600 rounded mx-auto" />
      <div className="flex justify-center gap-4 mt-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="w-6 h-6 bg-gray-300 dark:bg-gray-600 rounded-full"
          />
        ))}
      </div>
    </div>
  </div>
);

const ArticlePage = () => {
  const { slug } = useParams();
  const decodedSlug = slug ? decodeURIComponent(slug as string) : "";

  const {
    data: blog,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["blogPost", decodedSlug],
    queryFn: () => getBlogPostBySlug(decodedSlug),
    enabled: !!decodedSlug,
  });

  if (isLoading)
    return (
      <p className="text-center">
        <ArticleSkeleton />
      </p>
    );
  if (isError || !blog)
    return (
      <p className="text-center text-red-500">حدث خطأ أثناء تحميل المقال</p>
    );

  return (
    <div className="max-w-3xl mx-auto p-4 dark:bg-[#0B1739] space-y-10 text-right">
      {/* Cover Image + Title */}
      <div className="relative w-full h-64 rounded-lg bg-[#0b1739] overflow-hidden">
        <Image
          src={blog.image || "/images/articles.jpg"}
          alt={blog.title}
          fill
          className="object-cover"
        />
        <div className="absolute inset-0 bg-black/40 flex flex-col justify-center items-center text-white p-4">
          <h1 className="text-2xl font-bold mb-1">{blog.title}</h1>
          <p className="text-sm">
            {new Date(blog.published_at).toLocaleDateString("ar-EG", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}{" "}
            · {blog.author?.preferred_name || blog.author?.full_name}
          </p>
        </div>
      </div>

      {/* Article Body */}
      <div className="text-justify leading-7 space-y-5">
        <div dangerouslySetInnerHTML={{ __html: blog.content }} />
      </div>

      {/* Author Card */}
      <div className="bg-gray-100 dark:bg-[#081028] text-center p-6 rounded-xl">
        <div className="flex justify-center h-[65px]">
          <Image
            src={blog.author?.profile_picture_url || "/images/signup.png"}
            alt="الكاتب"
            width={65}
            height={65}
            className="rounded-full object-cover overflow-hidden"
          />
        </div>
        <p className="font-bold mt-2">{blog.author?.preferred_name}</p>
        {blog.author?.bio && (
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {blog.author.bio}
          </p>
        )}
        <div className="flex justify-center gap-4 mt-4 text-gray-700 dark:text-white">
          {blog.author?.facebook_url && (
            <a
              href={blog.author?.facebook_url}
              aria-label="Facebook"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Facebook color="#074182" size={18} />
            </a>
          )}
          {blog.author?.linkedin_url && (
            <a
              href={blog.author?.linkedin_url}
              aria-label="LinkedIn"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Linkedin color="#074182" size={18} />
            </a>
          )}
          {blog.author?.twitter_url && (
            <a
              href={blog.author?.twitter_url}
              aria-label="Twitter"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Twitter color="#074182" size={18} />
            </a>
          )}
          {blog.author?.instagram_url && (
            <a href={blog.author?.instagram_url} aria-label="instagram">
              <Instagram color="#074182" size={18} />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArticlePage;
