from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import logging
from typing import Optional

from config.config import Config

logger = logging.getLogger(__name__)

class SMSService:
    """Service for sending SMS notifications using Twilio."""
    
    def __init__(self, account_sid: str = None, auth_token: str = None, from_number: str = None):
        """Initialize the SMS service.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            from_number: Twilio phone number to send from
        """
        self.config = Config()
        self.account_sid = account_sid or self.config.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or self.config.TWILIO_AUTH_TOKEN
        self.from_number = from_number or self.config.TWILIO_PHONE_NUMBER
        
        # Initialize Twilio client
        self.client = Client(self.account_sid, self.auth_token)
    
    def send_sms(
        self,
        to_number: str,
        message: str,
        from_number: str = None
    ) -> Optional[dict]:
        """Send an SMS message if ENABLE_SMS is True in config. Otherwise, skip and log."""
        if not self.config.ENABLE_SMS:
            logger.info(f"SMS sending disabled by config. Would send to {to_number}: {message}")
            return None
        """Send an SMS message.
        
        Args:
            to_number: Recipient's phone number in E.164 format
            message: Message content
            from_number: Sender's phone number (default: from config)
            
        Returns:
            Dictionary with message details if successful, None otherwise
        """
        from_number = from_number or self.from_number
        
        try:
            message = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to_number
            )
            
            logger.info(f"SMS sent to {to_number}. SID: {message.sid}")
            return {
                "sid": message.sid,
                "status": message.status,
                "to": message.to,
                "date_created": message.date_created.isoformat() if message.date_created else None
            }
            
        except TwilioRestException as e:
            logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error sending SMS: {str(e)}")
            return None
    
    def notify_team(
        self,
        message: str,
        team_number: str = None
    ) -> Optional[dict]:
        """Send a notification to the team.
        
        Args:
            message: Message content
            team_number: Team phone number (default: from config)
            
        Returns:
            Dictionary with message details if successful, None otherwise
        """
        team_number = team_number or self.config.TEAM_NOTIFICATION_PHONE
        if not team_number:
            logger.warning("No team notification number configured")
            return None
            
        return self.send_sms(to_number=team_number, message=message)

# Singleton instance
sms_service = SMSService()
