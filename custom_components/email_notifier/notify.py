# ***********************************************************************************************************************************************
# Purpose:  Email (SMTP) notification service.
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
"""Mail (SMTP) notification service."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.components.notify import (
    PLATFORM_SCHEMA as NOTIFY_PLATFORM_SCHEMA,
    BaseNotificationService,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SENDER,
    CONF_TIMEOUT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEBUG,
    CONF_ENCRYPTION,
    CONF_RECIPIENTS,
    CONF_SENDER_NAME,
    CONF_SERVER,
    DEFAULT_DEBUG,
    DEFAULT_ENCRYPTION,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DOMAIN,
    ENCRYPTION_OPTIONS,
    GLOBAL_COUNTER,
)

PLATFORMS = [Platform.NOTIFY]

PLATFORM_SCHEMA = NOTIFY_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_RECIPIENTS): vol.All(cv.ensure_list, [vol.Email]),
        vol.Required(CONF_SENDER): vol.Email,
        vol.Optional(CONF_SERVER, default=DEFAULT_HOST): cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        vol.Optional(CONF_ENCRYPTION, default=DEFAULT_ENCRYPTION): vol.In(ENCRYPTION_OPTIONS),
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SENDER_NAME): cv.string,
        vol.Optional(CONF_DEBUG, default=DEFAULT_DEBUG): cv.boolean,
        vol.Optional(CONF_VERIFY_SSL, default=True): cv.boolean,
    }
)


# ***********************************************************************************************************************************************
# Purpose:  Setup service (ever called?)
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
# def async_get_service(
#     hass: HomeAssistant,
#     config: ConfigType,
#     discovery_info: DiscoveryInfoType | None = None,
# ) -> MailNotificationService | None:
#     """Get the mail notification service."""
#     setup_reload_service(hass, DOMAIN, PLATFORMS)
#     mail_service = MailNotificationService(
#         config[CONF_SERVER],
#         config[CONF_PORT],
#         config[CONF_TIMEOUT],
#         config[CONF_SENDER],
#         config[CONF_ENCRYPTION],
#         config.get(CONF_USERNAME),
#         config.get(CONF_PASSWORD),
#         config[CONF_RECIPIENTS],
#         config.get(CONF_SENDER_NAME),
#         config[CONF_DEBUG],
#         config[CONF_VERIFY_SSL],
#         0
#     )
#     #Test connection
#     if mail_service.connection_is_valid():
#         return mail_service

#     return None


# ***********************************************************************************************************************************************
# Purpose:  Setup email client entity (runs when Home Assist is started or when the integration is added)
# History:  D.Geisenhoff    24-JAN-2025     Created
# ***********************************************************************************************************************************************
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    ) -> None:
    """Set up the notify platform."""
    notify_service = MailNotificationService(hass, config_entry)
    # Store the notify service in hass.data (no need to store as entity id, because there is only one entity per entry)
    hass.data[DOMAIN][config_entry.entry_id] = notify_service
    async_add_entities([notify_service])
    api = hass.data[DOMAIN]['api']
    return api.connection_is_valid(config_entry.data)


# ***********************************************************************************************************************************************
# Purpose:  E-Mail service and entity class
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
class MailNotificationService(BaseNotificationService, Entity):
    """Implement the notification service for E-mail messages."""

    _attr_has_entity_name = True

    # ***********************************************************************************************************************************************
    # Purpose:  Initialize the class
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the SMTP service."""
        super().__init__()
        self.hass = hass
        self.config_entry = config_entry
        self.tries = 2
        self._attr_unique_id = f"email_notification_{config_entry.entry_id}"
        self.entity_id = f"notify.email_notification_sender_{hass.data[DOMAIN][GLOBAL_COUNTER]}"
        self._set_entity_name()
        # Add a listener for config changes and remove when entity is unloaded
        config_entry.async_on_unload(config_entry.add_update_listener(self._async_update_options))


    # ***********************************************************************************************************************************************
    # Purpose:  Run when entity is about to be added to hass (not used here).
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    async def async_added_to_hass(self) -> None:
        """Run when entity is about to be added to hass."""
        await super().async_added_to_hass()


    # ***********************************************************************************************************************************************
    # Purpose:  Run when entity will be removed from hass (not used here).
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        await super().async_will_remove_from_hass()


    # ***********************************************************************************************************************************************
    # Purpose:  Update sender placeholder for the entity name
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    def _set_entity_name(self) -> None:
        "Update the sender for the entity name."
        # Be aware that the backend language is taken, not the frontend language, this is mostly 'en'!
        # self._attr_translation_key = "entity_name"
        # self._attr_translation_placeholders = {"sender": self.config_entry.options.get(CONF_SENDER, self.config_entry.data.get(CONF_SENDER))}
        self._attr_name = "Sender email account: " + (self.config_entry.options.get("sender", self.config_entry.data.get("sender")) or "")


    # ***********************************************************************************************************************************************
    # Purpose:  Update entity name, when configuration changes (config options)
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    async def _async_update_options(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Update entry title and entity name."""
        self._set_entity_name()
        self.async_write_ha_state()


    # ***********************************************************************************************************************************************
    # Purpose:  No polling
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    @property
    def should_poll(self) -> bool:
        """Return the polling state."""
        return False


    # ***********************************************************************************************************************************************
    # Purpose:  Send message by using this entity as target and send to default recipient(s). Uses notify.send_message sevice
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    async def _async_send_message(self, message: str = "", **kwargs: vol.Any) -> None:
        """Send a message to a recipient."""
        self.state = 'sending'
        api = self.hass.data[DOMAIN]['api']
        await api.send_message(message, kwargs.get("title","Home Assistant"), self.config_entry.options if self.config_entry.options else self.config_entry.data, kwargs)
        self.state = 'ready'


    # ***********************************************************************************************************************************************
    # Purpose:  Send message using form. Uses email_notification.send sevice
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    async def send_message(self, message="", title="Home Assistant", data=None):
        """Build and send a message to a user.

        Will send plain text normally, with pictures as attachments if images config is
        defined, or will build a multipart HTML if html config is defined.
        """
        self.state = 'sending'
        if data is None:
            data = {}
        api = self.hass.data[DOMAIN]['api']
        await api.send_message(message, title, self.config_entry.options if self.config_entry.options else self.config_entry.data, data)
        self.state = 'ready'
