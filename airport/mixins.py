from rest_framework import status
from rest_framework.response import Response


class ImageUploadMixin:
    def upload_image(self, request, pk=None):
        obj = self.get_object()
        serializer = self.get_serializer(
            obj,
            data=request.data
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
