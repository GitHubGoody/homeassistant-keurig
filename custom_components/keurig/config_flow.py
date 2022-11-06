"""Config flow for Keurig Connect integration."""
from __future__ import annotations

import logging
from homeassistant.const import CONF_USERNAME
import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from pykeurig.keurigapi import KeurigApi
from typing import Any
import voluptuous as vol
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Keurig Connect."""

    def __init__(self):

        self.data: dict = {}
        self._api = KeurigApi()
        self._brewers = None

    VERSION = 1

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            if not await self._api.login(
                user_input["username"], user_input["password"]
            ):
                errors["base"] = "invalid_auth"
            else:
                self._brewers = {
                    dev.id: dev.name for dev in await self._api.async_get_devices()
                }
                self.data = user_input
                return await self.async_step_devices()
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_devices(self, user_input: dict[str, Any] | None = None):
        """Handle brewer selection step."""
        if user_input is None:
            return self.async_show_form(
                step_id="devices",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            "brewers", default=list(self._brewers)
                        ): cv.multi_select(self._brewers)
                    }
                ),
            )
        else:
            self.data.update(user_input)
            return self.async_create_entry(
                title=self.data[CONF_USERNAME], data=self.data
            )
