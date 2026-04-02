from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from apps.access_control.permissions.IsAdminUser import IsAdminUser

from apps.hris.hris_core.selectors import LocationSelector, OrganizationSelector
from apps.hris.hris_core.services import LocationService, OrganizationService, EmployeeService
from apps.hris.hris_core.api.serializers import LocationSerializers, EmployeeListSerializer, EmployeeCreateSerializer
from apps.hris.hris_core.selectors.employee_selectors import EmployeeSelector
from apps.hris.hris_core.models.employee import Employee
from apps.hris.hris_core.models.base import Location
from apps.hris.hris_core.models.organization import Department, JobTitle

from apps.hris.hris_core.api.serializers import DepartmentSerializer,JobTitleSerializer

class LocationListCreateApiView(APIView):
    """
        UZB: Filiallar ro'yxatini olish va yangi filial yaratish uchun API.
        ENG: API to list all locations and create a new location.
    """
    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]



    def get(self, request):
        company_id = request.query_params.get('company_id', 1)

        locations = LocationSelector.get_locations_by_company(company_id=company_id)
        serializer = LocationSerializers(locations, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = LocationSerializers(data=request.data)
        if serializer.is_valid():
            """
            # UZB: Ma'lumot valid bo'lsa, Servis orqali bazaga saqlaymiz
            # ENG: If data is valid, save to database via Service
            """
            location = OrganizationService.create_location(
                **serializer.validated_data,
                company_id=request.data.get('company_id', 1)
            )
            return Response(LocationSerializers(location).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


#Location detail Api View
class LocationDetailApiView(APIView):

    """GET PATCH DELETE """
    def get_permissions(self):
        if self.request.method =="GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]


    def get(self, request, pk):
        location = get_object_or_404(
            Location, pk=pk, company_id=request.tenant.id, is_deleted=False
        )
        return Response (LocationSerializers(location).data)

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




# Department List APi View
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
            company_id=request.tenant.id,
            **serializer.validated_data
        )
        return Response(DepartmentSerializer(department).data,  status=status.HTTP_201_CREATED)



#Department  Detail api view
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
                **serializer.validated_data
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


#Job title List create  Api view

class JobTitleListCreateApiView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]


    def get(self, request):
        job_title = OrganizationSelector.get_job_titles_by_company(
            company_id=request.tenant.id
        )
        serializer = JobTitleSerializer(job_title, many=True)
        return Response(serializer.data)

    def post(self,  request):
        serializer = JobTitleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job_title = OrganizationService.create_job_title(
            company_id=request.tenant.id,
            **serializer.validated_data,
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


#______________________________________________________
# Employee List Create Api View
#_______________________________________________________

class EmployeeListCreateApiView(APIView):

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]


    serializer_class = EmployeeCreateSerializer
    def get(self, request):
        company_id = request.tenant.id
        employess = EmployeeSelector.get_employee_by_company(company_id=company_id)
        serializer = EmployeeListSerializer(employess, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = EmployeeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        company_id = request.tenant.id
        #Servis orqali hodim yaratamiz
        # create employees throught the servise
        employee = EmployeeService.create_employee(
            company_id = company_id,
            **serializer.validated_data
        )
        return  Response(
            EmployeeListSerializer(employee).data,
            status=status.HTTP_201_CREATED
        )


#----------------------------------------------------
# Employee DetailApi View
#-------------------------

class EmployeeDetailApiView(APIView):
    """
    Bitta xodimni ko'risho O'chirish tahrirlash va o'chirish
    get or Delete, a single employee by ID
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]


    serializer_class = EmployeeCreateSerializer

    def get(self, request, pk):
        employee =  get_object_or_404(Employee,pk=pk, company_id=request.tenant.id)
        serializer = EmployeeListSerializer(employee)
        return Response(serializer.data)

    def patch(self, request, pk):
        serializer = EmployeeCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            #servise
            updated_employee = EmployeeService.update_employee(
                employee_id=pk,
                company_id=request.tenant.id,
                **serializer.validated_data
            )
            return Response(EmployeeListSerializer(updated_employee).data)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            EmployeeService.delete_employee(
                employee_id=pk, company_id=request.tenant.id
            )
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)
