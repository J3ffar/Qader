import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function UserCardSkeleton() {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4 flex flex-col items-center text-center">
        <Skeleton className="h-20 w-20 rounded-full mb-4" />
        <Skeleton className="h-5 w-32 mb-2" />
        <Skeleton className="h-4 w-24" />
      </CardContent>
      <CardFooter className="p-2 bg-muted/50">
        <Skeleton className="h-10 w-full rounded-md" />
      </CardFooter>
    </Card>
  );
}
