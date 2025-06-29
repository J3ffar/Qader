"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface LatestBlogPostsProps {
  posts: {
    id: number;
    title: string;
    author: string;
    publishedAt: string;
  }[];
}

export default function LatestBlogPosts({ posts }: LatestBlogPostsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>أحدث المقالات</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>العنوان</TableHead>
              <TableHead>المؤلف</TableHead>
              <TableHead>تاريخ النشر</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {posts.map((post) => (
              <TableRow key={post.id}>
                <TableCell className="font-medium">{post.title}</TableCell>
                <TableCell>{post.author}</TableCell>
                <TableCell>{post.publishedAt}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}