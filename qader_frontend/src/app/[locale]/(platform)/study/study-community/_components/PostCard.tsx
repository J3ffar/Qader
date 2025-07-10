"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { CommunityPostList } from "@/types/api/community.types";
import { Heart, MessageSquare } from "lucide-react";
import Image from "next/image";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { togglePostLike } from "@/services/community.service";
import { toast } from "sonner";
import { queryKeys } from "@/constants/queryKeys";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";

interface PostCardProps {
  post: CommunityPostList;
}

export function PostCard({ post }: PostCardProps) {
  const queryClient = useQueryClient();

  const likeMutation = useMutation({
    mutationFn: () => togglePostLike(post.id),
    onMutate: async () => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({
        queryKey: queryKeys.community.posts.all(),
      });

      // Snapshot the previous value
      const previousData = queryClient.getQueryData(
        queryKeys.community.posts.list({})
      ); // Adjust filters if necessary

      // Optimistically update to the new value
      queryClient.setQueryData(
        queryKeys.community.posts.list({}),
        (oldData: any) => {
          if (!oldData) return oldData;
          return {
            ...oldData,
            pages: oldData.pages.map((page: any) => ({
              ...page,
              results: page.results.map((p: CommunityPostList) =>
                p.id === post.id
                  ? {
                      ...p,
                      is_liked_by_user: !p.is_liked_by_user,
                      like_count: p.is_liked_by_user
                        ? p.like_count - 1
                        : p.like_count + 1,
                    }
                  : p
              ),
            })),
          };
        }
      );

      return { previousData };
    },
    onError: (err, newTodo, context) => {
      // Rollback on error
      queryClient.setQueryData(
        queryKeys.community.posts.list({}),
        context?.previousData
      );
      toast.error("حدث خطأ ما، لم يتم تسجيل إعجابك.");
    },
    onSettled: () => {
      // Invalidate to re-sync with server state
      queryClient.invalidateQueries({
        queryKey: queryKeys.community.posts.all(),
      });
    },
  });

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center space-x-4 rtl:space-x-reverse">
          <Avatar>
            <AvatarImage
              src={post.author.profile_picture_url || undefined}
              alt={post.author.full_name || "المستخدم"}
            />
            <AvatarFallback>{post.author.full_name?.charAt(0)}</AvatarFallback>
          </Avatar>
          <div>
            <p className="font-semibold">{post.author.full_name}</p>
            <p className="text-sm text-muted-foreground">
              {post.author.grade} •{" "}
              {new Date(post.created_at).toLocaleDateString("ar-EG", {
                day: "numeric",
                month: "long",
              })}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <p className="mb-4 whitespace-pre-wrap">{post.content_excerpt}</p>
        {post.image_url && (
          <div className="relative w-full h-80 mb-4 rounded-lg overflow-hidden">
            <Image
              src={post.image_url}
              alt="Post image"
              layout="fill"
              objectFit="cover"
            />
          </div>
        )}
      </CardContent>
      <CardFooter className="flex flex-col items-start space-y-4">
        <div className="flex justify-between w-full text-sm text-muted-foreground">
          <span>{post.like_count} إعجاب</span>
          <span>{post.reply_count} تعليقات</span>
        </div>
        <div className="w-full border-t pt-2 grid grid-cols-2 gap-2">
          <Button
            variant="ghost"
            onClick={() => likeMutation.mutate()}
            disabled={likeMutation.isPending}
          >
            <Heart
              className={cn("me-2 h-4 w-4", {
                "fill-red-500 text-red-500": post.is_liked_by_user,
              })}
            />
            إعجاب
          </Button>
          <Button variant="ghost">
            <MessageSquare className="me-2 h-4 w-4" />
            تعليق
          </Button>
        </div>
        {/* Reply form and list would go here */}
        <div className="w-full flex items-center space-x-2 rtl:space-x-reverse">
          <Avatar className="h-8 w-8">{/* Current user avatar */}</Avatar>
          <Input placeholder="اكتب رد..." className="flex-1" />
          <Button size="sm">إرسال</Button>
        </div>
      </CardFooter>
    </Card>
  );
}
