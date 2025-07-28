"use client";

import { Users, Newspaper, Activity, BarChart } from "lucide-react";
import AnalyticsCard from "@/components/features/admin/dashboard/AnalyticsCard";
import RecentActivity from "@/components/features/admin/dashboard/RecentActivity";
import LatestBlogPosts from "@/components/features/admin/dashboard/LatestBlogPosts";

export default function AdminDashboardPage() {
  // Mock data with hardcoded Arabic text
  const mockActivities = [
    {
      id: 1,
      user: { name: "علي أحمد", avatarUrl: "/avatars/01.png" },
      action: "قام بالتسجيل.",
      timestamp: "قبل 10 دقائق",
    },
    {
      id: 2,
      user: { name: "فاطمة حسن", avatarUrl: "/avatars/02.png" },
      action: "نشر مقالاً جديداً.",
      timestamp: "قبل ساعة",
    },
    {
      id: 3,
      user: { name: "خالد إبراهيم", avatarUrl: "/avatars/03.png" },
      action: "أكمل تحدياً.",
      timestamp: "قبل 3 ساعات",
    },
  ];

  const mockBlogPosts = [
    {
      id: 1,
      title: "مستقبل الذكاء الاصطناعي في التعليم",
      author: "د. عائشة الفارسي",
      publishedAt: "2025-06-28",
    },
    {
      id: 2,
      title: "التلعيب في تدريب الشركات",
      author: "محمد البلوشي",
      publishedAt: "2025-06-27",
    },
    {
      id: 3,
      title: "دليل للتعلم الفعال عن بعد",
      author: "سلمى الحارثي",
      publishedAt: "2025-06-25",
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          لوحة التحكم الرئيسية
        </h1>
        <p className="text-muted-foreground">
          عرض عام للإحصائيات والأنشطة الأخيرة.
        </p>
      </div>

      {/* Analytics Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <AnalyticsCard title="إجمالي المستخدمين" value="1,250" icon={Users} />
        <AnalyticsCard title="المقالات المنشورة" value="50" icon={Newspaper} />
        <AnalyticsCard title="التحديات النشطة" value="12" icon={Activity} />
        <AnalyticsCard title="تفاعل المستخدمين" value="85%" icon={BarChart} />
      </div>

      {/* Main Content Area */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <div className="lg:col-span-4">
          <LatestBlogPosts posts={mockBlogPosts} />
        </div>
        <div className="lg:col-span-3">
          <RecentActivity activities={mockActivities} />
        </div>
      </div>
    </div>
  );
}
