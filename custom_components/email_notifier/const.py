# ***********************************************************************************************************************************************
# Purpose:  Constants for the Email Notification Service integration.
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
"""Constants for the Email Notification Service integration."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "email_notifier"
PLATFORM: Final = Platform.NOTIFY
GLOBAL_COUNTER = "counter"
GLOBAL_API = "api"

ATTR_IMAGES: Final = "images"  # optional embedded image file attachments
ATTR_HTML: Final = "html"
ATTR_SENDER_NAME: Final = "sender_name"

CONF_ENCRYPTION: Final = "encryption"
CONF_DEBUG: Final = "debug"
CONF_SERVER: Final = "server"
CONF_PORT: Final = "port"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_SENDER: Final = "sender"
CONF_RECIPIENTS: Final = "recipients"
CONF_SENDER_NAME: Final = "sender_name"
CONF_TIMEOUT: Final = "timeout"
CONF_TEST_CONNECTION: Final = "test_connection"

DEFAULT_HOST: Final = "localhost"
DEFAULT_PORT: Final = 587
DEFAULT_TIMEOUT: Final = 15
DEFAULT_DEBUG: Final = False
DEFAULT_ENCRYPTION: Final = "starttls"

ENCRYPTION_OPTIONS: Final = ["tls", "starttls", "none"]
