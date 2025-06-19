import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";

export default function SettingsPageSkeleton() {
  return (
    <div className="space-y-6">
      <header>
        <Skeleton className="h-8 w-48" />
        <Skeleton className="mt-2 h-4 w-72" />
      </header>
      <Separator />

      {/* Tabs Skeleton */}
      <div className="flex space-x-4 border-b rtl:space-x-reverse">
        <Skeleton className="h-10 w-24" />
        <Skeleton className="h-10 w-24 bg-muted" />
        <Skeleton className="h-10 w-24 bg-muted" />
      </div>

      {/* Content Skeleton (mimicking Account Tab) */}
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-8">
          <div className="flex items-center gap-4">
            <Skeleton className="h-20 w-20 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-6 w-40" />
              <Skeleton className="h-8 w-32" />
            </div>
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-10 w-full" />
            </div>
            <div className="space-y-2">
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-10 w-full" />
            </div>
          </div>
          <Skeleton className="h-10 w-32 self-end" />
        </CardContent>
      </Card>
    </div>
  );
}
