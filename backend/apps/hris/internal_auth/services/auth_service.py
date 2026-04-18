"""
InternalAuthService
===================
Core authentication logic for internal (employee) logins.

Responsibilities:
  1. Normalize + validate identifier (email or username)
  2. Authenticate user (constant-time password check)
  3. Enforce account state (active, not deleted, not locked)
  4. Resolve company context (UserCompany)
  5. Resolve employee context (Employee + Employment)
  6. Aggregate permissions via PermissionResolver
  7. Determine redirect via RedirectResolver
  8. Generate enriched JWT via InternalTokenService
  9. Audit every attempt via InternalAuthAuditService

Does NOT:
  - Send OTPs
  - Handle 2FA (future extension point)
  - Touch the external auth flow
"""
import logging
from typing import Optional

from django.contrib.auth import get_user_model
from django.db.models import Q

from apps.access_control.models import UserCompany
from apps.shared.exceptions import BusinessException

from .permission_resolver import PermissionResolver
from .redirect_resolver import RedirectResolver
from .token_service import InternalTokenService
from .audit_service import InternalAuthAuditService

logger = logging.getLogger(__name__)
User = get_user_model()

# ── Failure reason constants (machine-readable, never exposed to client) ───────
_REASON_NOT_FOUND = "user_not_found"
_REASON_INACTIVE = "account_inactive"
_REASON_DELETED = "account_deleted"
_REASON_LOCKED = "account_locked"
_REASON_BAD_PASSWORD = "bad_password"
_REASON_NO_COMPANY = "no_active_company"
_REASON_COMPANY_INACTIVE = "company_inactive"
_REASON_EMPLOYEE_INACTIVE = "employee_inactive"

# Generic error message — never reveal which field is wrong
_GENERIC_ERROR = "Invalid credentials or account not authorized for internal access."


class InternalAuthService:

    # ── Public entry point ─────────────────────────────────────────────────────

    @staticmethod
    def login(
        identifier: str,
        password: str,
        company_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> dict:
        """
        Authenticate an internal user and return the full login response.

        Args:
            identifier:  Email or username (normalized before lookup).
            password:    Raw password (never logged).
            company_id:  Optional explicit company context. If None, resolved
                         from the user's primary active UserCompany.
            ip_address:  Client IP for audit logging.
            user_agent:  HTTP User-Agent for audit logging.

        Returns:
            Full login response dict (see _build_response).

        Raises:
            BusinessException: On any authentication or authorization failure.
                               The message is always the generic error string
                               to prevent user enumeration.
        """
        normalized = InternalAuthService._normalize_identifier(identifier)

        # 1. Resolve user
        user = InternalAuthService._get_user(normalized)
        if user is None:
            InternalAuthAuditService.record(
                identifier=normalized,
                outcome=InternalLoginAttempt.Outcome.FAILURE,
                failure_reason=_REASON_NOT_FOUND,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise BusinessException(_GENERIC_ERROR)

        # 2. Account state checks
        InternalAuthService._check_account_state(
            user, normalized, ip_address, user_agent
        )

        # 3. Password verification (constant-time via Django's check_password)
        if not user.check_password(password):
            InternalAuthService._handle_failed_password(
                user, normalized, ip_address, user_agent
            )
            raise BusinessException(_GENERIC_ERROR)

        # 4. Reset failed attempts on success
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=["failed_login_attempts", "locked_until"])

        # 5. Resolve company context
        resolved_company_id, company = InternalAuthService._resolve_company(
            user, company_id, normalized, ip_address, user_agent
        )

        # 6. Resolve employee context (optional — user may not have an employee record)
        employee_id, employment_status = InternalAuthService._resolve_employee(
            user, resolved_company_id
        )

        # 7. Aggregate permissions
        perm_data = PermissionResolver.resolve(user.pk, resolved_company_id)

        # 8. Redirect
        redirect = RedirectResolver.resolve(perm_data["roles"])

        # 9. Generate tokens
        tokens = InternalTokenService.generate_tokens(
            user=user,
            company_id=resolved_company_id,
            employee_id=employee_id,
            roles=perm_data["roles"],
            permissions=perm_data["permissions"],
            modules=perm_data["modules"],
        )

        # 10. Audit success
        InternalAuthAuditService.record(
            identifier=normalized,
            outcome=InternalLoginAttempt.Outcome.SUCCESS,
            user=user,
            company_id=resolved_company_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return InternalAuthService._build_response(
            user=user,
            company_id=resolved_company_id,
            employee_id=employee_id,
            perm_data=perm_data,
            tokens=tokens,
            redirect=redirect,
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_identifier(identifier: str) -> str:
        """Lowercase email, strip whitespace from username."""
        identifier = identifier.strip()
        if "@" in identifier:
            return identifier.lower()
        return identifier

    @staticmethod
    def _get_user(identifier: str):
        """Lookup by email or username. Returns None if not found."""
        return User.objects.filter(
            Q(email__iexact=identifier) | Q(username__iexact=identifier)
        ).first()

    @staticmethod
    def _check_account_state(user, identifier, ip_address, user_agent):
        """Raise BusinessException if account is not usable."""
        if user.is_deleted:
            InternalAuthAuditService.record(
                identifier=identifier,
                outcome=InternalLoginAttempt.Outcome.FAILURE,
                failure_reason=_REASON_DELETED,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise BusinessException(_GENERIC_ERROR)

        if not user.is_active:
            InternalAuthAuditService.record(
                identifier=identifier,
                outcome=InternalLoginAttempt.Outcome.FAILURE,
                failure_reason=_REASON_INACTIVE,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise BusinessException(_GENERIC_ERROR)

        if user.is_locked():
            InternalAuthAuditService.record(
                identifier=identifier,
                outcome=InternalLoginAttempt.Outcome.LOCKED,
                failure_reason=_REASON_LOCKED,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise BusinessException(
                "Account is temporarily locked due to too many failed attempts. "
                "Please try again later."
            )

    @staticmethod
    def _handle_failed_password(user, identifier, ip_address, user_agent):
        """Increment failed attempts, lock if threshold reached."""
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.lock_account(minutes=30)
            InternalAuthAuditService.record(
                identifier=identifier,
                outcome=InternalLoginAttempt.Outcome.LOCKED,
                failure_reason=_REASON_BAD_PASSWORD,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        else:
            user.save(update_fields=["failed_login_attempts"])
            InternalAuthAuditService.record(
                identifier=identifier,
                outcome=InternalLoginAttempt.Outcome.FAILURE,
                failure_reason=_REASON_BAD_PASSWORD,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
            )

    @staticmethod
    def _resolve_company(user, requested_company_id, identifier, ip_address, user_agent):
        """
        Resolve the active company context for this user.

        If requested_company_id is provided, verify the user belongs to it.
        Otherwise, use the primary active company.
        """
        uc_qs = UserCompany.objects.filter(
            user=user,
            is_active=True,
            is_deleted=False,
            company__status="active",
            company__is_deleted=False,
        ).select_related("company")

        if requested_company_id:
            uc = uc_qs.filter(company_id=requested_company_id).first()
        else:
            # Prefer primary company; fall back to first active
            uc = uc_qs.filter(is_primary_company=True).first() or uc_qs.first()

        if uc is None:
            InternalAuthAuditService.record(
                identifier=identifier,
                outcome=InternalLoginAttempt.Outcome.FAILURE,
                failure_reason=_REASON_NO_COMPANY,
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise BusinessException(_GENERIC_ERROR)

        return uc.company_id, uc.company

    @staticmethod
    def _resolve_employee(user, company_id) -> tuple[Optional[str], Optional[str]]:
        """
        Resolve employee record and active employment status.

        Returns:
            (employee_id_string, employment_status) or (None, None)
        """
        try:
            from apps.hris.hris_core.models import Employee, Employment

            employee = Employee.objects.filter(
                user_id=user.pk,
                company_id=company_id,
                is_deleted=False,
            ).first()

            if employee is None:
                return None, None

            # Get most recent active or probation employment
            employment = (
                Employment.objects.filter(
                    employee=employee,
                    status__in=[
                        Employment.StatusChoice.ACTIVE,
                        Employment.StatusChoice.PROBATION,
                    ],
                    is_deleted=False,
                )
                .order_by("-hire_date")
                .first()
            )

            if employment is None:
                # Employee exists but no active employment — still return employee_id
                # but log for visibility
                logger.info(
                    "Internal login: employee found but no active employment | "
                    "user_id=%s company_id=%s employee_id=%s",
                    user.pk, company_id, employee.employee_id,
                )
                return employee.employee_id, None

            return employee.employee_id, employment.status

        except Exception:
            logger.exception(
                "InternalAuthService._resolve_employee failed | user_id=%s", user.pk
            )
            return None, None

    @staticmethod
    def _build_response(user, company_id, employee_id, perm_data, tokens, redirect) -> dict:
        """Assemble the final login response contract."""
        return {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "token_type": tokens["token_type"],
            "expires_in": tokens["expires_in"],
            "user": {
                "id": user.pk,
                "account_uid": user.account_uid,
                "email": user.email,
                "full_name": user.full_name,
                "company_id": company_id,
                "employee_id": employee_id,
                "roles": perm_data["roles"],
                "permissions": perm_data["permissions"],
                "modules": perm_data["modules"],
            },
            "redirect": redirect,
        }


# Deferred import to avoid circular import at module load time
from ..models import InternalLoginAttempt  # noqa: E402
