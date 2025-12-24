# ***********************************************************************************************************************************************
# Purpose:  Config flow for Email Client integration
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
"""Config flow for Email Client integration."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowContext
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

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
    DEFAULT_ENCRYPTION,
    DEFAULT_PORT,
    DEFAULT_TIMEOUT,
    DOMAIN,
    ENCRYPTION_OPTIONS,
    GLOBAL_API,
)
from .smtp_api import SmtpAPI


# ***********************************************************************************************************************************************
# Purpose:  Test connection
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
def _test_connection(hass: HomeAssistant, user_input) -> bool:
    """Test the connection with the provided user input."""
    if DOMAIN not in hass.data:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][GLOBAL_API] = SmtpAPI(hass)
    api = hass.data[DOMAIN][GLOBAL_API]
    return api.connection_is_valid(user_input, True)



# ***********************************************************************************************************************************************
# Purpose:  Get config flow schema
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
def get_schema(self, user_input: dict[str, Any] | None) -> vol.Schema:
    """Return schema."""
    if user_input is None:
        user_input = {}
    if hasattr(self, "_entry"):
        config_entry = self._entry
    else:
        config_entry =  SimpleNamespace()
        config_entry.options = {}
        config_entry.data = {}
    return vol.Schema(
    {
        vol.Required(
            CONF_SERVER,
            default = user_input.get(CONF_SERVER,config_entry.options.get(CONF_SERVER, config_entry.data.get(CONF_SERVER))),
        ): str,
        vol.Required(
            CONF_PORT,
            default = user_input.get(CONF_PORT,config_entry.options.get(CONF_PORT, config_entry.data.get(CONF_PORT, DEFAULT_PORT))),
        ): int,
        vol.Required(
            CONF_USERNAME,
            default = user_input.get(CONF_USERNAME, config_entry.options.get(CONF_USERNAME, config_entry.data.get(CONF_USERNAME))),
        ): str,
        vol.Required(
            CONF_PASSWORD,
            default = user_input.get(CONF_PASSWORD, config_entry.options.get(CONF_PASSWORD, config_entry.data.get(CONF_PASSWORD))),
        ): str,
        vol.Required(
            CONF_SENDER,
            default = user_input.get(CONF_SENDER, config_entry.options.get(CONF_SENDER, config_entry.data.get(CONF_SENDER))),
        ): str,
        vol.Required(
            CONF_RECIPIENTS,
            default = user_input.get(CONF_RECIPIENTS, config_entry.options.get(CONF_RECIPIENTS, config_entry.data.get(CONF_RECIPIENTS))),
        ): str,
        vol.Optional(
            CONF_SENDER_NAME,
            default = user_input.get(CONF_SENDER_NAME, config_entry.options.get(CONF_SENDER_NAME, config_entry.data.get(CONF_SENDER_NAME,"Home Assistant"))),
        ): str,
        vol.Required(
                CONF_ENCRYPTION,
                default = user_input.get(CONF_ENCRYPTION, config_entry.options.get(CONF_ENCRYPTION, config_entry.data.get(CONF_ENCRYPTION, DEFAULT_ENCRYPTION))),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options =  ENCRYPTION_OPTIONS,
                    translation_key = CONF_ENCRYPTION,
            )),
        vol.Required(
            CONF_TIMEOUT,
            default = user_input.get(CONF_TIMEOUT, config_entry.options.get(CONF_TIMEOUT, config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT))),
        ): int,
        vol.Optional(CONF_TEST_CONNECTION, default = False): bool,
    })



# ***********************************************************************************************************************************************
# Purpose:  Configuration form for the integration (runs when integration entry is added)
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
class EmailClientConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Email Client."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult[ConfigFlowContext, str]:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input.get(CONF_TEST_CONNECTION):
                if not _test_connection(self.hass,user_input):
                    errors["base"] = "connection_failed"
                    return self.async_show_form(step_id="user", data_schema=get_schema(self, user_input), errors=errors)
            return self.async_create_entry(title=user_input[CONF_SENDER], data=user_input)

        return self.async_show_form(step_id="user", data_schema=get_schema(self, user_input), errors=errors)


    # ***********************************************************************************************************************************************
    # Purpose:  Callback from options flow (must be inside class, otherwise the 'Configuration' link will not be displayed)
    # History:  D.Geisenhoff    24-JAN-2025     Created
    # ***********************************************************************************************************************************************
    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return EmailClientOptionsFlow(config_entry)

    @property
    def _title_placeholders(self) -> dict[str, str]:
        """Return title placeholders für die Entry."""
        return {"email": "test@microteq.ch"}


# ***********************************************************************************************************************************************
# Purpose:  Configuration form for options (runs when configuration link is clicked)
# History:  D.Geisenhoff    07-MAY-2025     Created
# ***********************************************************************************************************************************************
class EmailClientOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    # ***********************************************************************************************************************************************
    # Purpose:  Initialize the class.
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = config_entry

    # ***********************************************************************************************************************************************
    # Purpose:  Show first (and in this case only) step of config form
    # History:  D.Geisenhoff    07-MAY-2025     Created
    # ***********************************************************************************************************************************************
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult[ConfigFlowContext, str]:
        """Manage the options."""
        if user_input is not None:
            if user_input.get(CONF_TEST_CONNECTION):
                if not _test_connection(self.hass,user_input):
                    return self.async_show_form(
                        step_id="init",
                        data_schema=get_schema(self, user_input),
                        errors={"base": "connection_failed"},
                    )
            # Merge user_input and config_entry.data into new dictionary and save back to config_entry.data
            # config_entry.option is not needed, because the info for creating an entry (data) and for editing an entry (option) is the same.
            new_data = {**self._entry.data, **user_input}
            # async_update_entry saves the new changes
            self.hass.config_entries.async_update_entry(self._entry, data=new_data, title = user_input[CONF_SENDER])
            # Save back an empty object to config_entry.options
            return self.async_create_entry(title="", data = {})
        return self.async_show_form(step_id="init", data_schema=get_schema(self, user_input))
