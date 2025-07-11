// src/components/features/platform/support/UserSupportPage.tsx
"use client";

import { useQuery } from "@tanstack/react-query";
import { CreateSupportTicketForm } from "./CreateSupportTicketForm";
import { SupportTicketList } from "./SupportTicketList";
import { SupportTicketListSkeleton } from "./SupportTicketListSkeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { queryKeys } from "@/constants/queryKeys";
import { getUserSupportTickets } from "@/services/support.service";
import FaqSection from "./FaqSection"; // We'll create this reusable component
import type { FaqPageData } from "@/types/api/content.types";

interface UserSupportPageProps {
  initialFaqData: FaqPageData | null;
}

export function UserSupportPage({ initialFaqData }: UserSupportPageProps) {
  const {
    data: ticketsData,
    isLoading,
    isError,
  } = useQuery({
    queryKey: queryKeys.user.support.list(),
    queryFn: () => getUserSupportTickets(),
  });

  return (
    <div className="space-y-8 p-4 md:p-6" dir="rtl">
      {/* 1. FAQ Section - Reusing logic in a dedicated component */}
      <FaqSection initialData={initialFaqData} />

      <div className="grid gap-8 lg:grid-cols-5 lg:gap-12">
        {/* 2. Create Ticket Form */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>ابدأ محادثة مع الإدارة</CardTitle>
            </CardHeader>
            <CardContent>
              <CreateSupportTicketForm />
            </CardContent>
          </Card>
        </div>

        {/* 3. Ticket History */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <CardTitle>سجل حالات الدعم الإداري</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <SupportTicketListSkeleton />
              ) : isError ? (
                <p className="text-destructive text-center">
                  حدث خطأ أثناء تحميل التذاكر.
                </p>
              ) : (
                <SupportTicketList tickets={ticketsData?.results ?? []} />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
