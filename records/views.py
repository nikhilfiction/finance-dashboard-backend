from rest_framework import generics, status, filters
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .models import FinancialRecord
from .serializers import (
    FinancialRecordSerializer,
    FinancialRecordCreateSerializer,
    FinancialRecordUpdateSerializer,
)
from .filters import FinancialRecordFilter
from users.permissions import IsAdmin, IsAnyAuthenticatedRole


@extend_schema(tags=['Records'])
class FinancialRecordListCreateView(generics.ListCreateAPIView):
    # GET is open to all roles, POST is admin only
    # supports filtering by type, category, date range, amount range
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FinancialRecordFilter
    search_fields = ['description', 'notes', 'category']
    ordering_fields = ['date', 'amount', 'created_at', 'record_type', 'category']
    ordering = ['-date']

    def get_queryset(self):
        # excludes soft deleted records
        return FinancialRecord.active.select_related('created_by').all()

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdmin()]
        return [IsAnyAuthenticatedRole()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FinancialRecordCreateSerializer
        return FinancialRecordSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = FinancialRecordSerializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            paginated.data['success'] = True
            return paginated
        serializer = FinancialRecordSerializer(queryset, many=True)
        return Response({"success": True, "count": queryset.count(), "data": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = FinancialRecordCreateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response(
            {
                "success": True,
                "message": "Financial record created successfully.",
                "data": FinancialRecordSerializer(record).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=['Records'])
class FinancialRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    # view/edit/delete a single record - delete is soft delete only

    def get_queryset(self):
        return FinancialRecord.active.select_related('created_by').all()

    def get_permissions(self):
        if self.request.method in ('PUT', 'PATCH', 'DELETE'):
            return [IsAdmin()]
        return [IsAnyAuthenticatedRole()]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return FinancialRecordUpdateSerializer
        return FinancialRecordSerializer

    def retrieve(self, request, *args, **kwargs):
        record = self.get_object()
        return Response({"success": True, "data": FinancialRecordSerializer(record).data})

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        record = self.get_object()
        serializer = FinancialRecordUpdateSerializer(record, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "success": True,
            "message": "Record updated successfully.",
            "data": FinancialRecordSerializer(record).data,
        })

    def destroy(self, request, *args, **kwargs):
        # soft delete - just flags it, doesnt actually remove from db
        record = self.get_object()
        record.is_deleted = True
        record.save()
        return Response(
            {"success": True, "message": "Record deleted successfully."},
            status=status.HTTP_200_OK,
        )
