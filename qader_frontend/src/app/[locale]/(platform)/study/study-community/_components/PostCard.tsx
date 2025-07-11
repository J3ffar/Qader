"use client";

import { useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { CommunityPostList } from "@/types/api/community.types";
import { Heart, MessageSquare, Lock, Loader2 } from "lucide-react";
import Image from "next/image";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getPostDetails, togglePostLike } from "@/services/community.service";
import { toast } from "sonner";
import { queryKeys } from "@/constants/queryKeys";
import { cn } from "@/lib/utils";
import { formatRelativeTime } from "@/utils/time";
import { CreateReplyForm } from "./CreateReplyForm";
import { ReplyList } from "./ReplyList";

interface PostCardProps {
  post: CommunityPostList;
  listQueryKey: readonly unknown[];
}

const SECTION_LABELS: Record<string, string> = {
  verbal: "القسم اللفظي",
  quantitative: "القسم الكمي",
};

export function PostCard({ post: initialPost, listQueryKey }: PostCardProps) {
  const [isCommentsOpen, setIsCommentsOpen] = useState(false);
  const [showFullContent, setShowFullContent] = useState(false);
  const queryClient = useQueryClient();

  // Fetch detailed post data only when comments are opened or "read more" is clicked
  const { data: detailedPost, isLoading: isLoadingDetails } = useQuery({
    queryKey: queryKeys.community.postDetails.detail(initialPost.id),
    queryFn: () => getPostDetails(initialPost.id),
    enabled: isCommentsOpen || showFullContent, // Only fetch when needed
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Use detailed data if available, otherwise fall back to list data
  const post = detailedPost || initialPost;
  const content = showFullContent
    ? detailedPost?.content || initialPost.content_excerpt
    : initialPost.content_excerpt;
  const canShowReadMore =
    !showFullContent &&
    detailedPost?.content &&
    detailedPost.content.length > initialPost.content_excerpt.length;

  const likeMutation = useMutation({
    mutationFn: () => togglePostLike(post.id),
    onMutate: async () => {
      // Use the passed-in query key for precision
      await queryClient.cancelQueries({ queryKey: listQueryKey });
      const previousData = queryClient.getQueryData(listQueryKey);

      queryClient.setQueryData(listQueryKey, (oldData: any) => {
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
      });

      return { previousData };
    },
    onError: (err, newTodo, context) => {
      queryClient.setQueryData(listQueryKey, context?.previousData);
      toast.error("حدث خطأ ما، لم يتم تسجيل إعجابك.");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: listQueryKey });
    },
  });

  const handleToggleComments = () => {
    setIsCommentsOpen((prev) => !prev);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex items-center space-x-4 rtl:space-x-reverse">
            <Avatar>
              <AvatarImage
                src={post.author.profile_picture_url || undefined}
                alt={post.author.full_name || "المستخدم"}
              />
              <AvatarFallback>
                {post.author.full_name?.charAt(0)}
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="font-semibold">{post.author.full_name}</p>
              <p
                className="text-sm text-muted-foreground"
                title={new Date(post.created_at).toLocaleString()}
              >
                {formatRelativeTime(post.created_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {post.section_filter && (
              <Badge variant="outline">
                {SECTION_LABELS[post.section_filter.slug] ||
                  post.section_filter.name}
              </Badge>
            )}
            {post.is_closed && (
              <Badge variant="secondary">
                <Lock className="me-1 h-3 w-3" />
                مغلق
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {post.title && <h3 className="text-lg font-bold mb-2">{post.title}</h3>}

        <p className="whitespace-pre-wrap">
          {content}
          {canShowReadMore && (
            <button
              onClick={() => setShowFullContent(true)}
              className="text-primary font-semibold hover:underline ms-1"
            >
              ...اقرأ المزيد
            </button>
          )}
        </p>

        {post.image && (
          <div className="relative w-full h-80 mt-4 rounded-lg overflow-hidden">
            <Image
              src={post.image}
              alt={post.title || "Post image"}
              layout="fill"
              objectFit="cover"
            />
          </div>
        )}
      </CardContent>
      <CardFooter className="flex flex-col items-start space-y-2">
        <div className="flex justify-between w-full text-sm text-muted-foreground">
          <span>{post.like_count} إعجاب</span>
          <button onClick={handleToggleComments} className="hover:underline">
            {post.reply_count} تعليقات
          </button>
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
          <Button variant="ghost" onClick={handleToggleComments}>
            <MessageSquare className="me-2 h-4 w-4" />
            {isCommentsOpen ? "إخفاء الردود" : "عرض الردود"}
          </Button>
        </div>

        {isCommentsOpen && (
          <div className="w-full border-t pt-4">
            {isLoadingDetails ? (
              <div className="flex justify-center items-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            ) : (
              <>
                <CreateReplyForm postId={post.id} isClosed={post.is_closed} />
                <ReplyList postId={post.id} isPostClosed={post.is_closed} />
              </>
            )}
          </div>
        )}
      </CardFooter>
    </Card>
  );
}
