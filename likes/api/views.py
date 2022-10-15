from rest_framework import status
from rest_framework import filters
from rest_framework.generics import ListAPIView, CreateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated

from likes.api.pagination import get_pagination_class
from likes.api.serializers import (
    LikeListSerializer,
    LikeToggleSerializer,
    LikeContentTypeSerializer
)
from likes.models import Like
from likes.selectors import get_liked_object_ids
from likes.services import get_user_likes_count, is_object_liked_by_user

__all__ = (
    'LikedCountAPIView',
    'LikedIDsAPIView',
    'LikeToggleView',
    'LikeListAPIView',
)


class LikedCountAPIView(APIView):
    """
    API View to return count of likes for authenticated user.
    """
    permission_classes = (AllowAny, )

    def get(self, request, *args, **kwargs):
        serializer = LikeContentTypeSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        return Response(
            data={
                'count': get_user_likes_count(
                    user=request.user,
                    content_type=(
                        serializer.validated_data.get(
                            'type'
                        )
                    )
                )
            }
        )


class LikedIDsAPIView(APIView):
    """
    post:
    API View to return liked objects ids for a given user.
    if id is given, return is_liked to show if user liked the obje or not
    Possible payload:\n
    {
        "type": "app_label.model",  // object's content type's natural key joined string
        "id": 1  // optional object's primary key
    }
    """
    permission_classes = (AllowAny, )

    def get(self, request, *args, **kwargs):
        serializer = LikeContentTypeSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)
        data = dict()
        object_id = request.GET.get('id')
        content_type = serializer.validated_data.get('type')
        if object_id:
            user=request.user
            is_liked = Like.objects.filter(
                sender = user,
                content_type = content_type,
                object_id = object_id
            ).exists() if user.is_authenticated else False
            data={
                'ids':[int(object_id)] if is_liked else [],
                'is_liked': is_liked,
                # return likes count of t
                'all_likes_count': Like.objects.filter(
                        content_type = content_type,
                        object_id = object_id
                ).count()
            }
        else:
            data = {
                'ids': get_liked_object_ids(
                    user=self.request.user,
                    content_type=content_type,
                )
            }

        return Response(
            data=data
        )


class LikeToggleView(CreateAPIView):
    """
    post:
    API View to like-unlike given object by authenticated user.\n
    Possible payload:\n
        {
            "type": "app_label.model",  // object's content type's natural key joined string
            "id": 1  // object's primary key
        }
    """
    permission_classes = (IsAuthenticated, )
    serializer_class = LikeToggleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        data = serializer.data
        data['is_liked'] = getattr(serializer, 'is_liked', True)
        return Response(
            data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data)
        )


class LikeListAPIView(ListAPIView):
    """
    List API View to return all likes for authenticated user.
    """
    pagination_class = get_pagination_class()
    permission_classes = (IsAuthenticated, )
    serializer_class = LikeListSerializer
    queryset = Like.objects.all()
    filter_backends = (filters.SearchFilter, )
    search_fields = (
        'content_type__model',
    )

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                sender=self.request.user
            )
            .select_related('sender')
            .distinct()
        )
