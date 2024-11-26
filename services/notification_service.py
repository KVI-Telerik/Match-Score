import logging
from services.email_service import send_general_notification_email





def notify_user_added_to_event(user, event_type, event_details):
    """
    Notify a user that they have been added to a match or tournament.

    :param user: User object with 'email' and 'name'
    :param event_type: Either 'match' or 'tournament'
    :param event_details: Details of the match or tournament
    """
    subject = f"You've been added to a {event_type}!"
    content = (
        f"Hello {user['name']},\n\n"
        f"You have been added to the following {event_type}:\n{event_details}"
    )
    try:
        send_general_notification_email(user['email'], user['name'], subject, content)
    except Exception as e:
        logging.error(f"Failed to notify {user['email']} about {event_type} addition: {e}")


def notify_event_details_changed(users, event_type, updated_details):
    """
    Notify users that the details of a match or tournament have changed.

    :param users: List of user objects with 'email' and 'name'
    :param event_type: Either 'match' or 'tournament'
    :param updated_details: Updated details of the event
    """
    subject = f"{event_type.capitalize()} Details Updated"
    content = f"The details of the {event_type} have been updated:\n{updated_details}"
    
    for user in users:
        try:
            send_general_notification_email(user['email'], user['name'], subject, content)
        except Exception as e:
            logging.error(f"Failed to notify {user['email']} about {event_type} update: {e}")
            
def notify_user_request_handled(user, request_type, approved):
    """
    Notify a user that their request has been approved or declined.

    :param user: User object with 'email' and 'name'
    :param request_type: Type of request (e.g., 'promotion', 'profile-link')
    :param approved: Boolean indicating if the request was approved
    """
    status = "approved" if approved else "declined"
    subject = f"Your {request_type.capitalize()} Request Has Been {status.capitalize()}"
    content = (
        f"Hello {user['name']},\n\n"
        f"Your {request_type} request has been {status}."
    )
    try:
        send_general_notification_email(user['email'], user['name'], subject, content)
    except Exception as e:
        logging.error(f"Failed to notify {user['email']} about {request_type} request: {e}")