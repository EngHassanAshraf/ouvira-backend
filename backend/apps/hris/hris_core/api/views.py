# placeholder

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from apps.access_control.permissions.IsAdminUser import IsAdminUser
from apps.access_control.permissions.HasModulePermission import make_permission

# Granular HRIS permission classes
_CanBulkArchive = make_permission("employee.bulk_archive")
_CanBulkRestore = make_permission("employee.bulk_restore")
_CanImport      = make_permission("employee.import")
_CanExport      = make_permission("employee.export")

from apps.hris.hris_core.selectors import LocationSelector, OrganizationSelector
from apps.hris.hris_core.selectors.employment_selector import EmploymentSelector
from apps.hris.hris_core.selectors.employee_selectors import EmployeeSelector
from apps.hris.hris_core.selectors.attendance_selectors import AttendanceSelector
from apps.hris.hris_core.selectors.employee_filters import apply_employee_filters

from apps.hris.hris_core.api.serializers import (
    LocationSerializers,
    EmployeeListSerializer,
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer,
    EmployeeDetailSerializer,
    EmploymentSerializer,
    PositionSerializer,
    AttendanceSerializer,
    DepartmentSerializer,
    JobTitleSerializer,
    EmployeeLeaveBalanceSerializer,
    EmployeeAllowanceSerializer,
    EmployeeBankDetailSerializer,
    EmployeeCostSerializer,
    EmployeeDocumentSerializer,
)

from apps.hris.hris_core.models.employee import Employee
from apps.hris.hris_core.models.base import Location
from apps.hris.hris_core.models.organization import Department, JobTitle, Position
from apps.hris.hris_core.models.employment import Employment
from apps.hris.hris_core.models.attendance import AttendanceRecord
from apps.hris.hris_core.models.employee_extensions import (
    EmployeeLeaveBalance,
    EmployeeAllowance,
    EmployeeBankDetail,
    EmployeeCost,
    EmployeeDocument,
)

from apps.hris.hris_core.services import (
    EmploymentService,
    LocationService,
    OrganizationService,
    EmployeeService,
    EmployeeLeaveBalanceService,
    EmployeeAllowanceService,
    EmployeeBankDetailService,
    EmployeeCostService,
    EmployeeDocumentService,
    BulkArchiveService,
    BulkRestoreService,
    EmployeeImportService,
    EmployeeExportService,
)
from apps.hris.hris_core.services.attendance_services import AttendanceService


# ── Pagination ─────────────────────────────────────────────────────────────────

class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


# ── Helpers ────────────────────────────────────────────────────────────────────
# apply_employee_filters is imported from selectors.employee_filters and used
# directly below — no local re-definition needed.


# ── Location ───────────────────────────────────────────────────────────────────

class LocationListCreateApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request):
        company_id = request.tenant.id
        locations = LocationSelector.get_locations_by_company(company_id=company_id)
        serializer = LocationSerializers(locations, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = LocationSerializers(data=request.data)
        if serializer.is_valid():
            location = LocationService.create_location(
                **serializer.validated_data,
                company_id=request.tenant.id,
            )
            return Response(LocationSerializers(location).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LocationDetailApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request, pk):
        location = get_object_or_404(
            Location, pk=pk, company_id=request.tenant.id, is_deleted=False
        )
        return Response(LocationSerializers(location).data)

    def patch(self, request, pk):
        serializer = LocationSerializers(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            location = LocationService.update_location(
                location_id=pk,
                company_id=request.tenant.id,
                **serializer.validated_data,
            )
            return Response(LocationSerializers(location).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            LocationService.delete_location(location_id=pk, company_id=request.tenant.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


# ── Department ─────────────────────────────────────────────────────────────────

class DepartmentListCreateApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request):
        departments = OrganizationSelector.get_departments_by_company(
            company_id=request.tenant.id
        )
        serializer = DepartmentSerializer(departments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DepartmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = OrganizationService.create_department(
            company_id=request.tenant.id, **serializer.validated_data
        )
        return Response(DepartmentSerializer(department).data, status=status.HTTP_201_CREATED)


class DepartmentDetailApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request, pk):
        department = get_object_or_404(
            Department, pk=pk, company_id=request.tenant.id, is_deleted=False
        )
        return Response(DepartmentSerializer(department).data)

    def patch(self, request, pk):
        serializer = DepartmentSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            department = OrganizationService.update_department(
                department_id=pk,
                company_id=request.tenant.id,
                **serializer.validated_data,
            )
            return Response(DepartmentSerializer(department).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            OrganizationService.delete_department(
                department_id=pk, company_id=request.tenant.id
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


# ── Job Title ──────────────────────────────────────────────────────────────────

class JobTitleListCreateApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request):
        job_titles = OrganizationSelector.get_job_titles_by_company(
            company_id=request.tenant.id
        )
        serializer = JobTitleSerializer(job_titles, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = JobTitleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job_title = OrganizationService.create_job_title(
            company_id=request.tenant.id, **serializer.validated_data
        )
        return Response(JobTitleSerializer(job_title).data, status=status.HTTP_201_CREATED)


class JobTitleDetailApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request, pk):
        job_title = get_object_or_404(
            JobTitle, pk=pk, company_id=request.tenant.id, is_deleted=False
        )
        return Response(JobTitleSerializer(job_title).data)

    def patch(self, request, pk):
        serializer = JobTitleSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            job_title = OrganizationService.update_job_title(
                job_title_id=pk,
                company_id=request.tenant.id,
                **serializer.validated_data,
            )
            return Response(JobTitleSerializer(job_title).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            OrganizationService.delete_job_title(
                job_title_id=pk, company_id=request.tenant.id
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


# ── Position ───────────────────────────────────────────────────────────────────

class PositionListCreateApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request):
        positions = OrganizationSelector.get_positions_by_company(
            company_id=request.tenant.id
        )
        serializer = PositionSerializer(positions, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PositionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        position = OrganizationService.create_position(
            company_id=request.tenant.id, **serializer.validated_data
        )
        return Response(PositionSerializer(position).data, status=status.HTTP_201_CREATED)


class PositionDetailApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request, pk):
        position = get_object_or_404(
            Position, pk=pk, company_id=request.tenant.id, is_deleted=False
        )
        return Response(PositionSerializer(position).data)

    def patch(self, request, pk):
        serializer = PositionSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            position = OrganizationService.update_position(
                position_id=pk,
                company_id=request.tenant.id,
                **serializer.validated_data,
            )
            return Response(PositionSerializer(position).data)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            OrganizationService.delete_position(
                position_id=pk, company_id=request.tenant.id
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)


from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

# ── Employee ───────────────────────────────────────────────────────────────────

class EmployeeListCreateApiView(ListAPIView):
    """
    GET  /employees/  — paginated, filterable, sortable list
    POST /employees/  — create employee

    Filters  : ?search= ?nationality= ?department= ?employment_status=
    Ordering : ?ordering=first_name|-first_name|employee_id|nationality|created_at|updated_at
    """
    serializer_class = EmployeeListSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "nationality": ["exact", "icontains"],
        "department":  ["exact"],
        "is_deleted":  ["exact"],
    }
    search_fields = [
        "first_name", "last_name", "employee_id",
        "national_id", "personal_email", "contact_number",
    ]
    ordering_fields = ["employee_id", "first_name", "nationality", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get_queryset(self):
        company_id = self.request.tenant.id
        qs = EmployeeSelector.get_employee_by_company(company_id=company_id)
        return apply_employee_filters(qs, self.request.query_params)

    # Override post so the same URL handles create
    def post(self, request, *args, **kwargs):
        serializer = EmployeeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = EmployeeService.create_employee(
            company_id=request.tenant.id, **serializer.validated_data
        )
        return Response(
            EmployeeDetailSerializer(employee).data,
            status=status.HTTP_201_CREATED,
        )


class EmployeeDetailApiView(APIView):
    """
    GET   /employees/<pk>/  — full profile
    PATCH /employees/<pk>/  — partial update
    DELETE /employees/<pk>/ — soft-delete (archive)
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request, pk):
        try:
            employee = EmployeeSelector.get_employee_detail(
                employee_id=pk, company_id=request.tenant.id
            )
        except Employee.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmployeeDetailSerializer(employee).data)

    def patch(self, request, pk):
        serializer = EmployeeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            employee = EmployeeService.update_employee(
                employee_id=pk,
                company_id=request.tenant.id,
                **serializer.validated_data,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmployeeDetailSerializer(employee).data)

    def delete(self, request, pk):
        try:
            EmployeeService.delete_employee(
                employee_id=pk, company_id=request.tenant.id
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


class EmployeeArchiveListApiView(ListAPIView):
    """
    GET /employees/archived/  — paginated list of soft-deleted employees.
    Filters  : ?search= ?nationality= ?department= ?employment_status=
    Ordering : ?ordering=first_name|nationality|deleted_at
    """
    serializer_class = EmployeeListSerializer
    pagination_class = StandardPagination
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "nationality": ["exact", "icontains"],
        "department":  ["exact"],
    }
    search_fields = ["first_name", "last_name", "employee_id", "national_id"]
    ordering_fields = ["first_name", "nationality", "deleted_at"]
    ordering = ["-deleted_at"]

    def get_queryset(self):
        company_id = self.request.tenant.id
        qs = EmployeeSelector.get_archived_employees(company_id=company_id)
        return apply_employee_filters(qs, self.request.query_params)


class EmployeeRestoreApiView(APIView):
    """
    POST /employees/<pk>/restore/  — unarchive a soft-deleted employee
    """

    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, pk):
        try:
            employee = EmployeeService.restore_employee(
                employee_id=pk, company_id=request.tenant.id
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmployeeDetailSerializer(employee).data)


# ── Employment ─────────────────────────────────────────────────────────────────

class EmploymentListCreateApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request, employee_pk):
        employments = EmploymentSelector.get_by_employee(employee_id=employee_pk)
        serializer = EmploymentSerializer(employments, many=True)
        return Response(serializer.data)

    def post(self, request, employee_pk):
        serializer = EmploymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employment = EmploymentService.create_employment(
            employee_id=employee_pk, **serializer.validated_data
        )
        return Response(EmploymentSerializer(employment).data, status=status.HTTP_201_CREATED)


class EmploymentDetailApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request, employee_pk, pk):
        employment = get_object_or_404(
            Employment, pk=pk, employee_id=employee_pk, is_deleted=False
        )
        return Response(EmploymentSerializer(employment).data)

    def patch(self, request, employee_pk, pk):
        serializer = EmploymentSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            employment = EmploymentService.update_employment(
                employment_id=pk,
                employee_id=employee_pk,
                **serializer.validated_data,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmploymentSerializer(employment).data)

    def delete(self, request, employee_pk, pk):
        try:
            EmploymentService.delete_employment(
                employment_id=pk, employee_id=employee_pk
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Leave Balance ──────────────────────────────────────────────────────────────

class EmployeeLeaveBalanceListCreateApiView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, employee_pk):
        balances = EmployeeLeaveBalance.objects.filter(
            employee_id=employee_pk, is_deleted=False
        ).select_related("leave_type")
        return Response(EmployeeLeaveBalanceSerializer(balances, many=True).data)

    def post(self, request, employee_pk):
        serializer = EmployeeLeaveBalanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        balance = EmployeeLeaveBalanceService.set_balance(
            employee_id=employee_pk, **serializer.validated_data
        )
        return Response(
            EmployeeLeaveBalanceSerializer(balance).data,
            status=status.HTTP_201_CREATED,
        )


class EmployeeLeaveBalanceDetailApiView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, employee_pk, pk):
        serializer = EmployeeLeaveBalanceSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            balance = EmployeeLeaveBalanceService.adjust_balance(
                balance_id=pk,
                employee_id=employee_pk,
                **serializer.validated_data,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmployeeLeaveBalanceSerializer(balance).data)

    def delete(self, request, employee_pk, pk):
        try:
            EmployeeLeaveBalanceService.delete_balance(
                balance_id=pk, employee_id=employee_pk
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Allowance ──────────────────────────────────────────────────────────────────

class EmployeeAllowanceListCreateApiView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, employee_pk):
        allowances = EmployeeAllowance.objects.filter(
            employee_id=employee_pk, is_deleted=False
        )
        return Response(EmployeeAllowanceSerializer(allowances, many=True).data)

    def post(self, request, employee_pk):
        serializer = EmployeeAllowanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        allowance = EmployeeAllowanceService.create_allowance(
            employee_id=employee_pk, **serializer.validated_data
        )
        return Response(
            EmployeeAllowanceSerializer(allowance).data,
            status=status.HTTP_201_CREATED,
        )


class EmployeeAllowanceDetailApiView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, employee_pk, pk):
        serializer = EmployeeAllowanceSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            allowance = EmployeeAllowanceService.update_allowance(
                allowance_id=pk,
                employee_id=employee_pk,
                **serializer.validated_data,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmployeeAllowanceSerializer(allowance).data)

    def delete(self, request, employee_pk, pk):
        try:
            EmployeeAllowanceService.delete_allowance(
                allowance_id=pk, employee_id=employee_pk
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Bank Detail ────────────────────────────────────────────────────────────────

class EmployeeBankDetailApiView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, employee_pk):
        try:
            detail = EmployeeBankDetail.objects.get(
                employee_id=employee_pk, is_deleted=False
            )
        except EmployeeBankDetail.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmployeeBankDetailSerializer(detail).data)

    def put(self, request, employee_pk):
        serializer = EmployeeBankDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        detail = EmployeeBankDetailService.set_bank_detail(
            employee_id=employee_pk, **serializer.validated_data
        )
        return Response(EmployeeBankDetailSerializer(detail).data)

    def delete(self, request, employee_pk):
        try:
            EmployeeBankDetailService.delete_bank_detail(employee_id=employee_pk)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Employee Cost ──────────────────────────────────────────────────────────────

class EmployeeCostListCreateApiView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, employee_pk):
        costs = EmployeeCost.objects.filter(
            employee_id=employee_pk, is_deleted=False
        )
        return Response(EmployeeCostSerializer(costs, many=True).data)

    def post(self, request, employee_pk):
        serializer = EmployeeCostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cost = EmployeeCostService.create_cost(
            employee_id=employee_pk, **serializer.validated_data
        )
        return Response(
            EmployeeCostSerializer(cost).data, status=status.HTTP_201_CREATED
        )


class EmployeeCostDetailApiView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def patch(self, request, employee_pk, pk):
        serializer = EmployeeCostSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            cost = EmployeeCostService.update_cost(
                cost_id=pk,
                employee_id=employee_pk,
                **serializer.validated_data,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(EmployeeCostSerializer(cost).data)

    def delete(self, request, employee_pk, pk):
        try:
            EmployeeCostService.delete_cost(cost_id=pk, employee_id=employee_pk)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Employee Document ──────────────────────────────────────────────────────────

class EmployeeDocumentListCreateApiView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, employee_pk):
        docs = EmployeeDocument.objects.filter(
            employee_id=employee_pk, is_deleted=False
        )
        return Response(EmployeeDocumentSerializer(docs, many=True).data)

    def post(self, request, employee_pk):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST
            )
        doc = EmployeeDocumentService.upload_document(
            employee_id=employee_pk, file=file
        )
        return Response(
            EmployeeDocumentSerializer(doc).data, status=status.HTTP_201_CREATED
        )


class EmployeeDocumentDetailApiView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, employee_pk, pk):
        try:
            EmployeeDocumentService.delete_document(
                document_id=pk, employee_id=employee_pk
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Attendance ─────────────────────────────────────────────────────────────────

class AttendanceListCreateApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request, employee_pk):
        attendances = AttendanceSelector.get_by_employee(employee_id=employee_pk)
        serializer = AttendanceSerializer(attendances, many=True)
        return Response(serializer.data)

    def post(self, request, employee_pk):
        serializer = AttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attendance = AttendanceService.check_in(
            employee_id=employee_pk,
            date=serializer.validated_data["date"],
            check_in_time=serializer.validated_data["check_in_time"],
        )
        return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)


class AttendanceDetailApiView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get(self, request, employee_pk, pk):
        attendance = get_object_or_404(
            AttendanceRecord, pk=pk, employee_id=employee_pk, is_deleted=False
        )
        return Response(AttendanceSerializer(attendance).data)

    def patch(self, request, employee_pk, pk):
        serializer = AttendanceSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            attendance = AttendanceService.update_attendance(
                attendance_id=pk,
                employee_id=employee_pk,
                **serializer.validated_data,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(AttendanceSerializer(attendance).data)

    def delete(self, request, employee_pk, pk):
        try:
            AttendanceService.delete_attendance(
                attendance_id=pk, employee_id=employee_pk
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Bulk Actions ───────────────────────────────────────────────────────────────


class EmployeeBulkArchiveApiView(APIView):
    """
    POST /employees/bulk-archive/
    Body: {"employee_ids": [1, 2, 3]}
    """
    permission_classes = [IsAuthenticated, _CanBulkArchive]

    def post(self, request):
        employee_ids = request.data.get("employee_ids", [])
        if not isinstance(employee_ids, list) or not employee_ids:
            return Response(
                {"detail": "Provide a non-empty list of employee_ids."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = BulkArchiveService.archive(
            company_id=request.tenant.id,
            employee_ids=employee_ids,
        )
        return Response(result, status=status.HTTP_200_OK)


class EmployeeBulkRestoreApiView(APIView):
    """
    POST /employees/bulk-restore/
    Body: {"employee_ids": [1, 2, 3]}
    """
    permission_classes = [IsAuthenticated, _CanBulkRestore]

    def post(self, request):
        employee_ids = request.data.get("employee_ids", [])
        if not isinstance(employee_ids, list) or not employee_ids:
            return Response(
                {"detail": "Provide a non-empty list of employee_ids."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        result = BulkRestoreService.restore(
            company_id=request.tenant.id,
            employee_ids=employee_ids,
        )
        return Response(result, status=status.HTTP_200_OK)


# ── Import ─────────────────────────────────────────────────────────────────────

class EmployeeImportApiView(APIView):
    """
    POST /employees/import/
    Multipart: file=<xlsx>
    Returns import summary: {added, errors, total_rows}
    """
    permission_classes = [IsAuthenticated, _CanImport]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"detail": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not file.name.endswith(".xlsx"):
            return Response(
                {"detail": "Only .xlsx files are accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            result = EmployeeImportService.import_from_excel(
                company_id=request.tenant.id,
                file=file,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except RuntimeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_501_NOT_IMPLEMENTED)
        return Response(result, status=status.HTTP_200_OK)


# ── Export ─────────────────────────────────────────────────────────────────────

class EmployeeExportApiView(APIView):
    """
    GET /employees/export/
    Returns a CSV file download.
    Supports the same query params as the employee list (search, nationality,
    department, employment_status).
    """
    permission_classes = [IsAuthenticated, _CanExport]

    def get(self, request):
        from django.http import StreamingHttpResponse

        buffer = EmployeeExportService.export_to_csv(
            company_id=request.tenant.id,
            filters=request.query_params,
        )
        response = StreamingHttpResponse(
            buffer,
            content_type="text/csv",
        )
        response["Content-Disposition"] = 'attachment; filename="employees.csv"'
        return response


# ── Full Employee Create (single-payload, all tabs) ────────────────────────────

from apps.hris.hris_core.api.serializers import EmployeeFullCreateSerializer
from apps.hris.hris_core.services import EmployeeFullCreateService


class EmployeeFullCreateApiView(APIView):
    """
    POST /employees/full/

    Accepts all form tabs in a single payload:
      {
        "employee_id": "s1001",
        "first_name": "Mohamed",
        "last_name": "Samy",
        "national_id": "1234567890",
        ...personal fields...

        "employment": {
          "hire_date": "2025-01-01",
          "status": "active",
          "employment_type": "full_time"
        },

        "allowances": [
          {"name": "Transportation Allowance", "value": "1200.00"},
          {"name": "Housing Allowance", "value": "2000.00"}
        ],

        "bank_detail": {
          "bank_iban": "SA0380000000608010167519",
          "bank_name": "QNB Bank"
        }
      }

    Returns the full employee profile (EmployeeDetailSerializer).
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        serializer = EmployeeFullCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            employee = EmployeeFullCreateService.create(
                company_id=request.tenant.id,
                validated_data=serializer.validated_data,
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Reload with full prefetch for the response
        from apps.hris.hris_core.selectors.employee_selectors import EmployeeSelector
        try:
            employee = EmployeeSelector.get_employee_detail(
                employee_id=employee.pk,
                company_id=request.tenant.id,
            )
        except Exception:
            pass  # Return the basic instance if detail fetch fails

        return Response(
            EmployeeDetailSerializer(employee).data,
            status=status.HTTP_201_CREATED,
        )
