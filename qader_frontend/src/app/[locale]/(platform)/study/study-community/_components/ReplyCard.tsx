import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Heart } from "lucide-react";
import { useState } from "react";
import { CreateReplyForm } from "./CreateReplyForm";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toggleReplyLike } from "@/services/community.service";
import { queryKeys } from "@/constants/queryKeys";
import { toast } from "sonner";
import { CommunityReply } from "@/types/api/community.types";
import { NestedReply } from "@/utils/replyUtils";
import { formatRelativeTime } from "@/utils/time"; // <-- IMPORT

interface ReplyCardProps {
  reply: NestedReply; // <-- USE NESTED TYPE
  isPostClosed: boolean;
}

export function ReplyCard({ reply, isPostClosed }: ReplyCardProps) {
  const [isReplying, setIsReplying] = useState(false);
  const queryClient = useQueryClient();

  const likeMutation = useMutation({
    mutationFn: () => toggleReplyLike(reply.id),
    onMutate: async () => {
      const queryKey = queryKeys.community.postDetails.replies(reply.post);
      await queryClient.cancelQueries({ queryKey });
      const previousReplies = queryClient.getQueryData(queryKey);

      queryClient.setQueryData(queryKey, (oldData: any) => ({
        ...oldData,
        pages: oldData.pages.map((page: any) => ({
          ...page,
          results: page.results.map((r: CommunityReply) =>
            r.id === reply.id
              ? {
                  ...r,
                  is_liked_by_user: !r.is_liked_by_user,
                  like_count: r.is_liked_by_user
                    ? r.like_count - 1
                    : r.like_count + 1,
                }
              : r
          ),
        })),
      }));
      return { previousReplies };
    },
    onError: (err, variables, context) => {
      queryClient.setQueryData(
        queryKeys.community.postDetails.replies(reply.post),
        context?.previousReplies
      );
      toast.error("فشل تسجيل الإعجاب.");
    },
    onSettled: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.community.postDetails.replies(reply.post),
      });
    },
  });

  return (
    <div className="flex space-x-3 rtl:space-x-reverse">
      <Avatar className="h-9 w-9 flex-shrink-0">
        <AvatarImage
          src={reply.author.profile_picture_url || undefined}
          alt={reply.author.full_name || "المستخدم"}
        />
        <AvatarFallback>{reply.author.full_name?.charAt(0)}</AvatarFallback>
      </Avatar>
      <div className="flex-1 space-y-2">
        {/* Main Reply Content */}
        <div>
          <div className="bg-muted rounded-xl p-3">
            <p className="font-semibold text-sm">{reply.author.full_name}</p>
            <p className="text-sm whitespace-pre-wrap">{reply.content}</p>
          </div>
          <div className="flex items-center space-x-3 rtl:space-x-reverse ps-3 text-xs mt-1">
            <button
              onClick={() => likeMutation.mutate()}
              className={cn("font-semibold hover:underline", {
                "text-primary": reply.is_liked_by_user,
              })}
            >
              إعجاب
            </button>
            {!isPostClosed && (
              <button
                onClick={() => setIsReplying(!isReplying)}
                className="font-semibold hover:underline"
              >
                رد
              </button>
            )}
            {" "}
            <span
              className="text-muted-foreground"
              title={new Date(reply.created_at).toLocaleString()}
            >
              {formatRelativeTime(reply.created_at)} {/* <-- USE FORMATTER */}
            </span>
            {reply.like_count > 0 && (
              <span className="flex items-center text-muted-foreground">
                <Heart className="h-3 w-3 fill-red-500 text-red-500 me-1" />{" "}
                {reply.like_count}
              </span>
            )}
          </div>
        </div>

        {/* Form for replying to this comment */}
        {isReplying && (
          <CreateReplyForm
            postId={reply.post}
            parentReplyId={reply.id}
            isClosed={isPostClosed}
            onReplySuccess={() => setIsReplying(false)}
            autoFocus
          />
        )}

        {/* Render Child Replies (The Thread) */}
        {reply.childReplies && reply.childReplies.length > 0 && (
          <div className="space-y-4 pt-2">
            {reply.childReplies.map((childReply) => (
              <ReplyCard
                key={childReply.id}
                reply={childReply}
                isPostClosed={isPostClosed}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
