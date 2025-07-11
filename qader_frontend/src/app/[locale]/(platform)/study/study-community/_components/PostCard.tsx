import { useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { CommunityPostList } from "@/types/api/community.types";
import { Heart, MessageSquare, Lock } from "lucide-react";
import Image from "next/image";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { togglePostLike } from "@/services/community.service";
import { toast } from "sonner";
import { queryKeys } from "@/constants/queryKeys";
import { cn } from "@/lib/utils";
import { ReplyList } from "./ReplyList";
import { CreateReplyForm } from "./CreateReplyForm";
import { Badge } from "@/components/ui/badge";

interface PostCardProps {
  post: CommunityPostList;
  listQueryKey: readonly unknown[];
}

export function PostCard({ post, listQueryKey }: PostCardProps) {
  const [isCommentsOpen, setIsCommentsOpen] = useState(false);
  const queryClient = useQueryClient();

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
              <p className="text-sm text-muted-foreground">
                {post.author.grade} •{" "}
                {new Date(post.created_at).toLocaleDateString("ar-EG", {
                  day: "numeric",
                  month: "long",
                })}
              </p>
            </div>
          </div>
          {post.is_closed && (
            <Badge variant="secondary">
              <Lock className="me-1 h-3 w-3" />
              مغلق
            </Badge>
          )}
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
      <CardFooter className="flex flex-col items-start space-y-2">
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
          <Button
            variant="ghost"
            onClick={() => setIsCommentsOpen(!isCommentsOpen)}
          >
            <MessageSquare className="me-2 h-4 w-4" />
            تعليق
          </Button>
        </div>

        {/* --- Conditional Rendering of Replies --- */}
        {isCommentsOpen && (
          <div className="w-full border-t pt-4">
            <CreateReplyForm postId={post.id} isClosed={post.is_closed} />
            <ReplyList postId={post.id} isPostClosed={post.is_closed} />
          </div>
        )}
      </CardFooter>
    </Card>
  );
}
