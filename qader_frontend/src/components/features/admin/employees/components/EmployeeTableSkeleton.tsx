import { Skeleton } from "@/components/ui/skeleton";
import { TableCell, TableRow } from "@/components/ui/table";

export function EmployeeTableSkeleton({ rows = 8 }: { rows?: number }) {
  return Array.from({ length: rows }).map((_, i) => (
    <TableRow key={i}>
      <TableCell className="w-[80px]">
        <Skeleton className="h-4 w-10" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-4 w-36" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-4 w-48" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-4 w-24" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-6 w-20 rounded-full" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-4 w-24" />
      </TableCell>
      <TableCell className="w-[50px]">
        <Skeleton className="h-8 w-8" />
      </TableCell>
    </TableRow>
  ));
}
