import logging
from services.email_service import send_general_notification_email





async def notify_user_added_to_event(user, event_type, event_details):
    """
    Notify a user that they have been added to a match or tournament.

    :param user: User object with 'email' and 'name'
    :param event_type: Either 'match' or 'tournament'
    :param event_details: Details of the match or tournament
    """
    user_id, user_name, user_email = user[0]
    subject = f"You've been added to a {event_type}!"
    content = (
        f"Hello Mr.{user_name},\n\n"
        f"You have been added to the following {event_type}:\non {event_details[0]}\n{event_details[1][0]} VS {event_details[1][1]}"
    )
    
    try:
        await send_general_notification_email(user_email, user_name , subject, content)
    except Exception as e:
        logging.error(f"Failed to notify {user_email} about {event_type} addition: {e}")


async def notify_user_request_handled(user, request_type, approved):
    """
    Notify a user that their request has been approved or declined.

    :param user: User object with 'email' and 'name'
    :param request_type: Type of request (e.g., 'promotion', 'profile-link')
    :param approved: Boolean indicating if the request was approved
    """
    user_id, user_name, user_email = user[0]
    status = "approved" if approved else "declined"
    subject = f"Your {request_type.capitalize()} Request Has Been {status.capitalize()}"
    content = (
        f"Hello Mr.{user_name},\n\n"
        f"Your {request_type} request has been {status}."
    )
    
    try:
        await send_general_notification_email(user_email, user_name, subject, content)
    except Exception as e:
        logging.error(f"Failed to notify {user_email} about {request_type} request: {e}")
            
