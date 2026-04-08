"""
hris_core_connector.py
-----------------------
Outbound Adapter (Integration Layer) for the Recruitment Module.

This is the ONLY file in the recruitment module that is allowed to import
from hris_core. It implements the HRISCorePort interface, enforcing strict
module boundaries. If hris_core changes its Employee model, only this file
needs to be updated — the application layer (services) stays unchanged.

Architecture:
  Recruitment (Application Layer)
    --> calls HRISCoreConnector (Integration Layer)
      --> calls hris_core.Employee (External Module)
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class EmployeeCreateDTO:
    """
    Data Transfer Object for creating an Employee.
    Decouples the recruitment domain from hris_core's model signature.
    """
    employee_id: str
    national_id: str
    first_name: str
    last_name: str
    company_id: int
    department_id: int
    personal_email: Optional[str] = None
    contact_number: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None


class HRISCoreConnector:
    """
    Outbound Adapter for the HRIS Core module.

    The recruitment application layer calls this class to create employees
    without knowing the implementation details of hris_core.
    """

    @staticmethod
    def create_employee(dto: EmployeeCreateDTO) -> int:
        """
        Creates an Employee record in hris_core and returns the new employee's PK.
        This is the single integration point between Recruitment and hris_core.
        """
        # Late import is intentional: isolates hris_core dependency to this file only.
        from apps.hris.hris_core.models.employee import Employee

        employee = Employee.objects.create(
            company_id=dto.company_id,
            department_id=dto.department_id,
            employee_id=dto.employee_id,
            national_id=dto.national_id,
            first_name=dto.first_name,
            last_name=dto.last_name,
            personal_email=dto.personal_email,
            contact_number=dto.contact_number,
            gender=dto.gender,
            date_of_birth=dto.date_of_birth,
        )

        logger.info(
            f"[HRISCoreConnector] Employee created: id={employee.id}, "
            f"employee_id={employee.employee_id}"
        )
        return employee.id
