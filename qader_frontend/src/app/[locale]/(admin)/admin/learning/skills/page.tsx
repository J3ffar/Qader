import { SkillsClient } from "@/components/features/admin/learning/skills/SkillsClient";
import { Skeleton } from "@/components/ui/skeleton";
import { Suspense } from "react";

function PageSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-10 w-32" />
      </div>
      <Skeleton className="h-96 w-full" />
    </div>
  );
}

export default function AdminSkillsPage() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <SkillsClient />
    </Suspense>
  );
}
