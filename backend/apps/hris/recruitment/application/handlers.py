import logging
from ..domain.events.dispatcher import dispatcher
from ..domain.events.events import HiringRequestApproved, HiringRequestRejected
from .services.job_advertisement_service import JobAdvertisementService

logger = logging.getLogger(__name__)

def handle_hiring_request_approved(event: HiringRequestApproved):
    """
    Handler for HiringRequestApproved event.
    Automatically creates a Job Advertisement draft when a request is approved.
    """
    logger.info(f"Hiring Request {event.request_id} for company {event.company_id} approved. Creating Job Ad draft.")
    
    try:
        JobAdvertisementService.create_from_request(event.request_id)
    except Exception as e:
        logger.error(f"Failed to auto-create Job Advertisement for request {event.request_id}: {str(e)}")

def handle_hiring_request_rejected(event: HiringRequestRejected):
    """Handler for HiringRequestRejected event."""
    logger.info(f"Hiring Request {event.request_id} rejected. Reason: {event.reason}")
    pass

def register_recruitment_handlers():
    """Register all domain event handlers for the recruitment module."""
    dispatcher.subscribe(HiringRequestApproved, handle_hiring_request_approved)
    dispatcher.subscribe(HiringRequestRejected, handle_hiring_request_rejected)
