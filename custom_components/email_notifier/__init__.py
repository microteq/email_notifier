# ***********************************************************************************************************************************************
# Purpose:  An email notification service integration
# History:  D.Geisenhoff    06-JUN-2025     Created
# ***********************************************************************************************************************************************
"""Email Notification Service integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import _LOGGER, ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, GLOBAL_API, GLOBAL_COUNTER, PLATFORM
from .smtp_api import SmtpAPI


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
        data["images"] = call.data.get("images")
    if call.data.get("account"):
        data["account"] = call.data.get("account")
    if call.data.get("recipients"):
        data["recipients"] = call.data.get("recipients")
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
                vol.Required("message"): str,
                vol.Optional("html"): str,
                vol.Optional("images"): [str],
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
