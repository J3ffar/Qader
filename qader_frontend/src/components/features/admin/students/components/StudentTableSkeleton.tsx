import { Skeleton } from "@/components/ui/skeleton";
import { TableCell, TableRow } from "@/components/ui/table";

interface StudentTableSkeletonProps {
  rows: number;
}

export function StudentTableSkeleton({ rows }: StudentTableSkeletonProps) {
  return Array.from({ length: rows }).map((_, i) => (
    <TableRow key={i}>
      <TableCell>
        <Skeleton className="h-4 w-12" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-4 w-36" />
      </TableCell>
      <TableCell className="hidden md:table-cell">
        <Skeleton className="h-4 w-56" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-5 w-5" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-6 w-16 rounded-md" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-6 w-24 rounded-full" />
      </TableCell>
      <TableCell className="hidden lg:table-cell">
        <Skeleton className="h-4 w-24" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-8 w-8" />
      </TableCell>
    </TableRow>
  ));
}
