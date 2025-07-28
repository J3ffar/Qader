import { SearchPartnerDialog } from "./SearchPartnerDialog";
import { UserCardSkeleton } from "./UserCardSkeleton";
import { UserCard } from "./UserCard";
import { Loader2 } from "lucide-react";
import { User } from "@/types/api/user.types";
import { searchPartners } from "@/services/community.service";
import { queryKeys } from "@/constants/queryKeys";
import { useIntersection } from "@mantine/hooks";
import { useMemo, useRef, useState, useEffect } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useDebounce } from "@/hooks/use-debounce";
import { PartnerRequestsDialog } from "@/app/[locale]/(platform)/study/study-community/_components/partner_search/PartnerRequestsDialog";

// A utility to remove keys with empty/null/undefined values
const cleanFilters = (obj: any) => {
  const newObj: any = {};
  for (const key in obj) {
    if (obj[key] !== null && obj[key] !== undefined && obj[key] !== "") {
      newObj[key] = obj[key];
    }
  }
  return newObj;
};

export function PartnerSearchPage() {
  const [filters, setFilters] = useState<{ name?: string; grade?: string }>({});
  const debouncedName = useDebounce(filters.name, 500);

  const queryFilters = useMemo(() => {
    const rawFilters = {
      ...filters,
      name: debouncedName,
    };
    return cleanFilters(rawFilters);
  }, [filters, debouncedName]);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
  } = useInfiniteQuery({
    queryKey: queryKeys.community.partners.list(queryFilters),
    queryFn: searchPartners,
    initialPageParam: "1",
    getNextPageParam: (lastPage) =>
      lastPage.next
        ? new URL(lastPage.next).searchParams.get("page")
        : undefined,
  });

  const lastUserRef = useRef<HTMLDivElement>(null);
  const { ref, entry } = useIntersection({
    root: document.body,
    threshold: 0.5,
  });

  useEffect(() => {
    if (entry?.isIntersecting && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [entry, fetchNextPage, hasNextPage, isFetchingNextPage]);

  const partners = data?.pages.flatMap((page) => page.results) ?? [];

  return (
    <div>
      <div className="p-4 bg-muted/50 rounded-lg flex items-center justify-between mb-6 flex-wrap gap-4">
        <p className="text-muted-foreground">
          ابحث عن زميل للتحديات أو آخر بين المتواجدين للتحدي.
        </p>
        <div className="flex gap-2">
          <SearchPartnerDialog
            onSearch={(newFilters) => setFilters(newFilters)}
          />
          <PartnerRequestsDialog />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {isLoading &&
          Array.from({ length: 8 }).map((_, i) => <UserCardSkeleton key={i} />)}

        {!isLoading &&
          partners.map((user: User, i) => {
            // Attach the ref to the *last* element in the list
            if (i === partners.length - 1) {
              return (
                <div key={user.id} ref={ref}>
                  <UserCard user={user} />
                </div>
              );
            }
            return <UserCard key={user.id} user={user} />;
          })}

        {!isLoading && !isError && partners.length === 0 && (
          <div className="col-span-full text-center text-muted-foreground py-10">
            <p>لم يتم العثور على زملاء يطابقون بحثك.</p>
            <p className="text-sm">حاول تغيير معايير البحث.</p>
          </div>
        )}
        {isError && (
          <p className="col-span-full text-center text-destructive py-10">
            حدث خطأ أثناء البحث عن الزملاء.
          </p>
        )}
      </div>

      {isFetchingNextPage && (
        <div className="flex justify-center items-center py-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      )}
    </div>
  );
}
