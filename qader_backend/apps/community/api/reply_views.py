from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view
from apps.community.models import CommunityReply
from apps.api.permissions import IsSubscribed

@extend_schema(tags=["Student Community"], summary="Toggle Like on Reply")
class CommunityReplyLikeToggleView(generics.GenericAPIView):
    """
    Toggles the like status for the current user on a specific reply.
    """
    queryset = CommunityReply.objects.all()
    permission_classes = [IsAuthenticated, IsSubscribed]
    lookup_url_kwarg = 'reply_pk'

    def post(self, request, *args, **kwargs):
        reply = self.get_object()
        user = request.user

        if user in reply.likes.all():
            reply.likes.remove(user)
            liked = False
        else:
            reply.likes.add(user)
            liked = True

        return Response({'status': 'like toggled', 'liked': liked})
