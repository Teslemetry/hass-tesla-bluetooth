"""Config flow for Tesla Bluetooth integration."""

from __future__ import annotations

import hashlib
from typing import Any

from tesla_fleet_api.exceptions import NotOnWhitelistFault, TeslaFleetError
from tesla_fleet_api.tesla.bluetooth import TeslaBluetooth
from tesla_fleet_api.tesla.vehicle.bluetooth import VehicleBluetooth
import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN, LOGGER, PRIVATE_KEY_FILE

CONF_VIN = "vin"


def validate(name: str) -> bool:
    """Validate the name of a Tesla device."""
    return len(name) == 18 and name[0] == "S" and name[17] in "CDRP"


class TeslaBluetoothConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tesla Bluetooth."""

    VERSION = 1
    _discovered_device: BluetoothServiceInfoBleak | None = None
    _vehicle: VehicleBluetooth | None = None

    def __init__(self) -> None:
        """Initialize the config flow."""

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""

        # if(SERVICE_UUID not in discovery_info.service_uuids):
        if not validate(discovery_info.name) and not discovery_info.name.startswith(
            "🔑"
        ):
            LOGGER.debug(
                "Ignored BT device: %s @ %s",
                discovery_info.name,
                discovery_info.address,
            )
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        # I could try find a better name here
        #
        LOGGER.debug(
            "Ready to setup: %s @ %s", discovery_info.name, discovery_info.address
        )

        self.context["title_placeholders"] = {"name": discovery_info.name}
        self._discovered_device = discovery_info

        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Get the vehicles VIN."""
        errors = {}
        if user_input is not None:
            vin = user_input[CONF_VIN]
            name = "S" + hashlib.sha1(vin.encode("utf-8")).hexdigest()[:16]
            for discovery_info in async_discovered_service_info(self.hass):
                if discovery_info.name.startswith(name):
                    self._discovered_device = discovery_info
                    await self.async_set_unique_id(discovery_info.address)
                    self._abort_if_unique_id_configured()
                    interface = TeslaBluetooth()
                    await interface.get_private_key(
                        self.hass.config.path(PRIVATE_KEY_FILE)
                    )
                    self._vehicle = interface.vehicles.createBluetooth(
                        vin, device=discovery_info.device
                    )
                    await self._vehicle.connect(device=discovery_info.device)
                    return await self.async_step_check()
            errors["base"] = "not_found"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_VIN): str,
                },
            ),
            errors=errors,
        )

    async def async_step_check(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Check if the key is whitelisted."""
        assert self._vehicle is not None
        assert self._discovered_device is not None

        try:
            await self._vehicle.handshakeVehicleSecurity()
        except NotOnWhitelistFault:
            return await self.async_step_instructions()
        except TeslaFleetError as err:
            LOGGER.error("Failed to connect to vehicle: %s", err)
            self.async_abort(reason="unknown_error")

        return self.async_create_entry(
            title=self._vehicle.vin,
            data={
                CONF_VIN: self._vehicle.vin,
                CONF_ADDRESS: self._discovered_device.address,
            },
        )

    async def async_step_instructions(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Instruct the user on how to authorize the key."""

        if user_input is not None:
            return await self.async_step_authorize()

        return self.async_show_form(step_id="instructions")

    async def async_step_authorize(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Install the private key."""

        assert self._vehicle is not None

        for i in range(10):
            LOGGER.debug("Attempt %s to pair vehicle", i + 1)
            try:
                await self._vehicle.pair()
                return await self.async_step_check()
            except TeslaFleetError as err:
                LOGGER.error("Failed to pair vehicle: %s", err)

        return self.async_show_form(step_id="instructions", errors={"base": "timeout"})

    async def async_step_abort(self, reason: str) -> ConfigFlowResult:
        """Abort the flow."""
        if self._vehicle:
            await self._vehicle.disconnect()
        return self.async_abort(reason=reason)
