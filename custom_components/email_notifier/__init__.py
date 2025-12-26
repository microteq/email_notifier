# ***********************************************************************************************************************************************
# Purpose:  An email notification service integration
# History:  D.Geisenhoff    06-JUN-2025 Created
#           D.Geisenhoff    26-DEC-2025 Merged pull request from onoffautomations:
#                                       - Updated service schema to include new fields
#                                       - Changed images and attachments to accept string input (multiline)
#                                       - Added parsing logic to convert multiline string input to lists
#                                       - Updated async_send_email() to pass new parameters
# ***********************************************************************************************************************************************
"""Email Notification Service integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import _LOGGER, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er, selector

from .const import (
    CONF_ENCRYPTION,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_RECIPIENTS,
    CONF_SENDER,
    CONF_SENDER_NAME,
    CONF_SERVER,
    CONF_TEST_CONNECTION,
    CONF_TIMEOUT,
    CONF_USERNAME,
    DOMAIN,
    ENCRYPTION_OPTIONS,
    GLOBAL_API,
    GLOBAL_COUNTER,
    PLATFORM,
)
from .smtp_api import SmtpAPI

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_SERVER): str,
                vol.Required(CONF_PORT): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_SENDER): str,
                vol.Required(CONF_RECIPIENTS): str,
                vol.Optional(CONF_SENDER_NAME): str,
                vol.Required(CONF_ENCRYPTION): selector.SelectSelector(selector.SelectSelectorConfig(
                    options =  ENCRYPTION_OPTIONS,
                    translation_key = CONF_ENCRYPTION)),
                vol.Required(CONF_TIMEOUT): int,
                vol.Optional(CONF_TEST_CONNECTION): bool
            }
        )
    },
    extra=vol.ALLOW_EXTRA,  # Allow additional keys in YAML
)


# ***********************************************************************************************************************************************
# Purpose:  Initialize global variables
# History:  D.Geisenhoff    29-MAY-2025     Created
# ***********************************************************************************************************************************************
def init_vars(hass: HomeAssistant):
    """Initialize global variables for the Whatsigram Messenger component."""
    # Set a global counter for the entity id (entity id should not change after entity has been created, so the name of the sender cannot be taken)
    # The entity id will be notify_whatsigram_recipient_1, ...recipient_2, ...
    if GLOBAL_COUNTER not in hass.data[DOMAIN]:
        hass.data[DOMAIN][GLOBAL_COUNTER] = 1
    else:
        hass.data[DOMAIN][GLOBAL_COUNTER] += 1


# ***********************************************************************************************************************************************
# Purpose:  Send message callback function of service
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
async def async_send_email(call):
    """Send an email."""
    data = {}
    if call.data.get("html"):
        data["html"] = call.data.get("html")
    if call.data.get("images"):
        # Parse multiline string input into list
        images_input = call.data.get("images")
        if isinstance(images_input, str):
            # Split by newlines and filter out empty lines
            data["images"] = [line.strip() for line in images_input.split('\n') if line.strip()]
        elif isinstance(images_input, list):
            data["images"] = images_input
    if call.data.get("attachments"):
        # Parse multiline string input into list
        attachments_input = call.data.get("attachments")
        if isinstance(attachments_input, str):
            # Split by newlines and filter out empty lines
            data["attachments"] = [line.strip() for line in attachments_input.split('\n') if line.strip()]
        elif isinstance(attachments_input, list):
            data["attachments"] = attachments_input
    if call.data.get("account"):
        data["account"] = call.data.get("account")
    if call.data.get("recipients"):
        data["recipients"] = call.data.get("recipients")
    if call.data.get("from_address"):
        data["from_address"] = call.data.get("from_address")
    if call.data.get("sender_name"):
        data["sender_name"] = call.data.get("sender_name")
    if call.data.get("reply_to"):
        data["reply_to"] = call.data.get("reply_to")
    # Get sender entity
    entity_reg = er.async_get(call.hass)
    entity = entity_reg.async_get(data["account"])
    if entity is None:
        _LOGGER.error("No entity found for account %s", data["account"])
        return
    # Run send_message function of entity
    await call.hass.data[DOMAIN][entity.config_entry_id].send_message(call.data.get("message", ""), call.data.get("title", "Home Assistant"), data)



# ***********************************************************************************************************************************************
# Purpose:  Setup when Home Assistant starts, can run after or before setup_entry
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
async def async_setup(hass, config):
    """Set up the component."""
    # Register the service
    if DOMAIN not in hass.data:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][GLOBAL_API] = SmtpAPI(hass)
    if "send_mail" in hass.services.async_services().get(DOMAIN, {}):
        _LOGGER.info(f"Service {DOMAIN}.{"send_mail"} ist bereits registriert.")
    hass.services.async_register(
        DOMAIN,
        "send",
        async_send_email,
        schema=vol.Schema(
            {
                vol.Required("account"): str,
                vol.Optional("recipients"): str,
                vol.Optional("title"): str,
                vol.Optional("message"): str,
                vol.Optional("html"): str,
                vol.Optional("images"): str,
                vol.Optional("attachments"): str,
                vol.Optional("from_address"): str,
                vol.Optional("sender_name"): str,
                vol.Optional("reply_to"): str,
            }
        ),
    )
    return True


# ***********************************************************************************************************************************************
# Purpose:  Setup entities. Run when Home Assist is started, or entry is added. Can run after or before setup
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Email Client from a config entry."""
    if DOMAIN not in hass.data:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][GLOBAL_API] = SmtpAPI(hass)
    init_vars(hass)
    hass.data[DOMAIN][entry.entry_id] = {}
    # Set up notify platform
    await hass.config_entries.async_forward_entry_setups(entry, [PLATFORM])
    # Add a listener for config changes and remove when entity is unloaded
    #entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


# ***********************************************************************************************************************************************
# Purpose:  Update entity name, when configuration changes
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
# async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
#     """Update entry title and entity name."""
#     hass.config_entries.async_update_entry(entry,title=entry.options.get("sender", entry.data.get("sender")))
#     entity_reg = er.async_get(hass)
#     entities = er.async_entries_for_config_entry(entity_reg, entry.entry_id)
#     entity_reg.async_update_entity(entities[0].entity_id, _attr_translation_placeholders = {"sender": entry.options.get("sender", entry.data.get("sender"))})


# ***********************************************************************************************************************************************
# Purpose:  Called when entry is unloaded
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_forward_entry_unload(entry, PLATFORM):
        hass.data[DOMAIN].pop(entry.entry_id)
        config_entries = hass.config_entries.async_entries(DOMAIN)
        num_entries = len(config_entries)
        if num_entries == 1:
            # Unregister the service, when last entry is removed
            hass.services.async_remove(DOMAIN, "send_email")
            # Remove all domain data
            hass.data.pop(DOMAIN)
    return unload_ok
