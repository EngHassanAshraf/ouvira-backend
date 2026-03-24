from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.hris.hris_core.selectors import LocationSelector, OrganizationSelector
from apps.hris.hris_core.services import LocationService, OrganizationService
from apps.hris.hris_core.api.serializers import LocationSerializers


class LocationListCreateApiView(APIView):
    """
        UZB: Filiallar ro'yxatini olish va yangi filial yaratish uchun API.
        ENG: API to list all locations and create a new location.
    """
    def get(self, request):
        company_id = request.query_params.get('company_id', 1)

        locations = OrganizationSelector.get_locations_by_company(company_id=company_id)
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
