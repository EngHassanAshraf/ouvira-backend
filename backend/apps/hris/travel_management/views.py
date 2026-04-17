from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from apps.access_control.permissions.IsAdminUser import IsAdminUser
from apps.hris.travel_management.models import TravelRequest
from apps.hris.travel_management.serializers import (
    TravelRequestSerializer,
    TravelRequestCreateSerializer,
)
from apps.hris.travel_management.services import TravelRequestService
from apps.hris.travel_management.selectors import TravelRequestSelector


class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class TravelRequestListCreateApiView(ListAPIView):
    """
    GET  /travel-requests/  — paginated, filterable list
    POST /travel-requests/  — submit a travel request

    Filters  : ?employee=<pk>
    Ordering : ?ordering=-created_at|start_date|end_date
    """
    serializer_class = TravelRequestSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "employee": ["exact"],
    }
    search_fields = ["employee__first_name", "employee__last_name", "destination"]
    ordering_fields = ["created_at", "start_date", "end_date"]
    ordering = ["-created_at"]

    def get_queryset(self):
        employee_id = self.request.query_params.get("employee")
        return TravelRequestSelector.get_all(
            employee_id=int(employee_id) if employee_id else None
        )

    def post(self, request, *args, **kwargs):
        serializer = TravelRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee_id = request.data.get("employee")
        if not employee_id:
            return Response(
                {"detail": "employee field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            req = TravelRequestService.create_request(
                employee_id=employee_id, **serializer.validated_data
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TravelRequestSerializer(req).data, status=status.HTTP_201_CREATED)


class TravelRequestDetailApiView(APIView):
    """
    GET    /travel-requests/<pk>/  — retrieve
    PATCH  /travel-requests/<pk>/  — update
    DELETE /travel-requests/<pk>/  — cancel (soft-delete)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        req = get_object_or_404(TravelRequest, pk=pk, is_deleted=False)
        return Response(TravelRequestSerializer(req).data)

    def patch(self, request, pk):
        serializer = TravelRequestCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        employee_id = request.data.get("employee")
        if not employee_id:
            return Response(
                {"detail": "employee field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            req = TravelRequestService.update_request(
                request_id=pk,
                employee_id=employee_id,
                **serializer.validated_data,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(TravelRequestSerializer(req).data)

    def delete(self, request, pk):
        employee_id = request.data.get("employee")
        if not employee_id:
            return Response(
                {"detail": "employee field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            TravelRequestService.delete_request(
                request_id=pk, employee_id=employee_id
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)
