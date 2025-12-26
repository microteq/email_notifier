# ***********************************************************************************************************************************************
# Purpose:      SMTP API class.
# Attribution:  Most of this code code is based on the Home Assistant SMTP integration.
# History:      D.Geisenhoff    07-MAY-2025 Created
#               D.Geisenhoff    26-DEC-2025 Merged pull request from onoffautomations:
#                                           - Added _download_file_from_url() function for remote file downloads
#                                           - Updated _attach_file() to handle both local files and URLs (made async)
#                                           - Updated _build_multipart_msg() to async
#                                           - Updated _build_html_msg() to async with URL filename extraction
#                                           - Modified send_message() to support custom from_address and reply_to headers
#                                           - Added support for attachments in all message types
# ***********************************************************************************************************************************************
"""SMTP API class."""

from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import email.utils
import logging
from pathlib import Path
import smtplib
import socket
from urllib.parse import urlparse

import aiohttp

from homeassistant.const import CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.util import dt as dt_util
from homeassistant.util.ssl import client_context

from .const import (
    ATTR_ATTACHMENTS,
    ATTR_FROM_ADDRESS,
    ATTR_HTML,
    ATTR_IMAGES,
    ATTR_REPLY_TO,
    CONF_DEBUG,
    CONF_ENCRYPTION,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_RECIPIENTS,
    CONF_SENDER,
    CONF_SENDER_NAME,
    CONF_SERVER,
    CONF_TIMEOUT,
    CONF_USERNAME,
    DEFAULT_DEBUG,
    DOMAIN,
    # ERROR_CONNECTION_FAILED,
    # ERROR_INVALID_KEY,
    # ERROR_NO_RECIPIENT,
    # ERROR_NO_TEXT,
    # ERROR_PAGE_NOT_FOUND,
    # ERROR_PERMISSION_DENIED,
    # ERROR_TEMP_UNAVAILABLE,
    # ERROR_UNKNOWN,
    # ERROR_WRONG_PARAMETER,
)

_LOGGER = logging.getLogger(__name__)


# ***********************************************************************************************************************************************
# Purpose:  CallMeBot Web API class
# History:  D.Geisenhoff    24-OCT-2024     Created
# ***********************************************************************************************************************************************
class SmtpAPI:
    """SMTP API class."""

    # ***********************************************************************************************************************************************
    # Purpose:  Initialize the class
    # History:  D.Geisenhoff    24-OCT-2024     Created
    # ***********************************************************************************************************************************************
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the class."""
        self.hass = hass
        self.config_data = {}
        self.tries = 2


    # ***********************************************************************************************************************************************
    # Purpose:  Connect to mail server
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    def connect(self, testConnection: bool = False):
        """Connect/authenticate to SMTP Server."""
        mail = None
        try:
            ssl_context = client_context() if self.config_data.get(CONF_VERIFY_SSL, True) else None
            if self.config_data[CONF_ENCRYPTION] == "tls":
                mail = smtplib.SMTP_SSL(
                    self.config_data[CONF_SERVER],
                    self.config_data[CONF_PORT],
                    timeout=self.config_data[CONF_TIMEOUT],
                    context=ssl_context,
                )
            else:
                mail = smtplib.SMTP(self.config_data[CONF_SERVER], self.config_data[CONF_PORT], timeout=self.config_data[CONF_TIMEOUT])
            mail.set_debuglevel(self.config_data.get(CONF_DEBUG,DEFAULT_DEBUG))
            mail.ehlo_or_helo_if_needed()
            if self.config_data[CONF_ENCRYPTION] == "starttls":
                mail.starttls(context=ssl_context)
                mail.ehlo()
            if self.config_data[CONF_USERNAME] and self.config_data[CONF_PASSWORD]:
                mail.login(self.config_data[CONF_USERNAME], self.config_data[CONF_PASSWORD])
        except (socket.gaierror, ConnectionRefusedError) as err:
            if self.hass and self.hass.states:
                _LOGGER.exception(
                    (
                    "SMTP server not found or refused connection (%s:%s). Please check"
                    " the IP address, hostname, and availability of your SMTP server."
                    ),
                    self.config_data[CONF_SERVER],
                    self.config_data[CONF_PORT]
                )
            if mail:
                mail.quit()
                mail = None
            if not testConnection:
                raise HomeAssistantError(
                    f"SMTP server not found or refused connection ({self.config_data[CONF_SERVER]}:{self.config_data[CONF_PORT]}). "
                    "Please check the IP address, hostname, and availability of your SMTP server.") from err
        except smtplib.SMTPAuthenticationError as err:
            _LOGGER.exception(
                  "Login not possible. Please check your setting and/or your credentials"
            )
            if mail:
                mail.quit()
                mail = None
            if not testConnection:
                raise HomeAssistantError(f"Login not possible. Please check your setting and/or your credentials: {err}") from err
        return mail


    # ***********************************************************************************************************************************************
    # Purpose:  Return true, if connection is successful, false otherwise.
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    def connection_is_valid(self, config_data, testConnection: bool = False) -> bool:
        """Check for valid config, verify connectivity."""
        self.config_data = config_data
        server = self.connect(testConnection)
        if server:
            server.quit()
            return True
        return False


    # ***********************************************************************************************************************************************
    # Purpose:  Send message using form. Uses email_notification.send sevice
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    async def send_message(self, message="", title="Home Assistant", config_data = {}, data = {}):
        """Build and send a message to a user.

        Will send plain text normally, with pictures as attachments if images config is
        defined, or will build a multipart HTML if html config is defined.
        """
        self.config_data = config_data
        if ATTR_HTML in data:
            # HTML text flag
            msg = await _build_html_msg(
                self.hass,
                message,
                data[ATTR_HTML],
                images=data.get(ATTR_IMAGES, []),
            )
        elif ATTR_IMAGES in data:
            # No HTML text, but image attachments
            msg = await _build_multipart_msg(
                self.hass, message, images=data.get(ATTR_IMAGES, [])
            )
        else:
            # Plain text or with attachments only
            if data.get(ATTR_ATTACHMENTS):
                # Plain text with attachments
                msg = await _build_multipart_msg(self.hass, message, images=[])
            else:
                # Plain text only
                msg = _build_text_msg(message)

        # Add general file attachments if provided (to any message type)
        if data.get(ATTR_ATTACHMENTS):
            for attach_path in data[ATTR_ATTACHMENTS]:
                attachment = await _attach_file(self.hass, attach_path)
                if attachment:
                    msg.attach(attachment)
        # Subject
        msg["Subject"] = title
        # Recipients: Send to recipients, if provided, otherwise send to default recipients of config
        if CONF_RECIPIENTS in data:
            msg["To"] = data[CONF_RECIPIENTS] if isinstance(data.get(CONF_RECIPIENTS), str) else ",".join(data[CONF_RECIPIENTS])
            recipient_list = [recipient.strip() for recipient in data[CONF_RECIPIENTS].split(",")] if isinstance(data.get(CONF_RECIPIENTS), str) else data[CONF_RECIPIENTS]
        else:
            msg["To"] = self.config_data[CONF_RECIPIENTS] if isinstance(self.config_data[CONF_RECIPIENTS], str) else ",".join(self.config_data[CONF_RECIPIENTS])
            recipient_list = [recipient.strip() for recipient in self.config_data[CONF_RECIPIENTS].split(",")] if isinstance(self.config_data[CONF_RECIPIENTS], str) else self.config_data[CONF_RECIPIENTS]
        # Sender: Use from_address from data if provided, otherwise use config sender
        if ATTR_FROM_ADDRESS in data:
            # Custom from address provided in data
            from_address = data[ATTR_FROM_ADDRESS]
            # Check if sender_name is also provided in data
            if "sender_name" in data:
                msg["From"] = f"{data['sender_name']} <{from_address}>"
            else:
                msg["From"] = from_address
        else:
            # Use config sender
            if self.config_data.get(CONF_SENDER_NAME):
                msg["From"] = f"{self.config_data[CONF_SENDER_NAME]} <{self.config_data[CONF_SENDER]}>"
            else:
                msg["From"] = self.config_data[CONF_SENDER]

        # Reply-To: Add reply-to header if provided
        if ATTR_REPLY_TO in data:
            msg["Reply-To"] = data[ATTR_REPLY_TO]

        msg["X-Mailer"] = "Home Assistant"
        msg["Date"] = email.utils.format_datetime(dt_util.now())
        msg["Message-Id"] = email.utils.make_msgid()

        return self._send_email(msg, recipient_list)


    # ***********************************************************************************************************************************************
    # Purpose:  Private send mail function
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    def _send_email(self, msg, recipients):
        """Send the message."""
        mail = self.connect()
        for _ in range(self.tries):
            try:
                if mail:
                    mail.sendmail(self.config_data[CONF_SENDER], recipients, msg.as_string())
                break
            except smtplib.SMTPServerDisconnected:
                _LOGGER.warning("SMTPServerDisconnected sending mail: retrying connection")
                if mail:
                    mail.quit()
                mail = self.connect()
            except smtplib.SMTPException:
                _LOGGER.warning("SMTPException sending mail: retrying connection")
                if mail:
                    mail.quit()
                mail = self.connect()
        if mail:
            mail.quit()


# ***********************************************************************************************************************************************
# Purpose:  Download file from URL
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
async def _download_file_from_url(url: str) -> tuple[bytes, str] | None:
    """Download file from URL and return content and filename."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.read()
                    # Try to get filename from URL
                    parsed_url = urlparse(url)
                    filename = Path(parsed_url.path).name
                    if not filename:
                        filename = "attachment"
                    return content, filename
                else:
                    _LOGGER.warning("Failed to download file from %s: HTTP %s", url, response.status)
                    return None
    except Exception as err:
        _LOGGER.warning("Error downloading file from %s: %s", url, err)
        return None


# ***********************************************************************************************************************************************
# Purpose:  Built plain text message
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
def _build_text_msg(message):
    """Build plaintext email."""
    _LOGGER.debug("Building plain text email")
    return MIMEText(message)


# ***********************************************************************************************************************************************
# Purpose:  Attach file to message
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
async def _attach_file(hass, atch_name, content_id=""):
    """Create a message attachment.

    Supports both local files and remote URLs (http/https).
    If MIMEImage is successful and content_id is passed (HTML), add images in-line.
    Otherwise add them as attachments.
    """
    # Check if it's a URL
    is_url = atch_name.startswith(('http://', 'https://'))

    if is_url:
        # Download file from URL
        result = await _download_file_from_url(atch_name)
        if result is None:
            return None
        file_bytes, file_name = result
    else:
        # Local file
        try:
            file_path = Path(atch_name).parent
            if file_path.exists() and not hass.config.is_allowed_path(
                str(file_path)
            ):
                allow_list = "allowlist_external_dirs"
                file_name = Path(atch_name).name
                url = "https://www.home-assistant.io/docs/configuration/basic/"
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="remote_path_not_allowed",
                    translation_placeholders={
                        "allow_list": allow_list,
                        "file_path": str(file_path),
                        "file_name": str(file_name),
                        "url": url,
                    },
                )
            with Path.open(atch_name, "rb") as attachment_file:
                file_bytes = attachment_file.read()
            file_name = Path(atch_name).name
        except FileNotFoundError:
            _LOGGER.warning(
                "Attachment not found: %s",
                atch_name
            )
            return None

    try:
        attachment = MIMEImage(file_bytes)
    except TypeError:
        _LOGGER.debug(
            "File is not an image, attaching as application: %s",
            atch_name,
        )
        attachment = MIMEApplication(file_bytes, Name=file_name)
        attachment["Content-Disposition"] = (
            f'attachment; filename="{file_name}"'
        )
    else:
        if content_id:
            attachment.add_header("Content-ID", f"<{content_id}>")
        else:
            attachment.add_header(
                "Content-Disposition",
                f"attachment; filename={file_name}",
            )

    return attachment


# ***********************************************************************************************************************************************
# Purpose:  Build multipart message with images as attachment
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
async def _build_multipart_msg(hass, message, images):
    """Build Multipart message with images as attachments."""
    _LOGGER.debug("Building multipart email with image attachment(s)")
    msg = MIMEMultipart()
    body_txt = MIMEText(message)
    msg.attach(body_txt)

    for atch_name in images:
        attachment = await _attach_file(hass, atch_name)
        if attachment:
            msg.attach(attachment)

    return msg


# ***********************************************************************************************************************************************
# Purpose:  Build Multipart message with in-line images and rich HTML (UTF-8)
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
async def _build_html_msg(hass, text, html, images):
    """Build Multipart message with in-line images and rich HTML (UTF-8)."""
    _LOGGER.debug("Building HTML rich email")
    msg = MIMEMultipart("related")
    alternative = MIMEMultipart("alternative")
    alternative.attach(MIMEText(text, _charset="utf-8"))
    alternative.attach(MIMEText(html, ATTR_HTML, _charset="utf-8"))
    msg.attach(alternative)

    for atch_name in images:
        # Extract filename from URL or path
        if atch_name.startswith(('http://', 'https://')):
            parsed_url = urlparse(atch_name)
            name = Path(parsed_url.path).name
        else:
            name = Path(atch_name).name
        attachment = await _attach_file(hass, atch_name, name)
        if attachment:
            msg.attach(attachment)
    return msg



