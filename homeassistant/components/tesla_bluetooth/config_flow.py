"""Config flow for Tesla Bluetooth integration."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any

from bleak.backends.device import BLEDevice
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


@dataclass
class Discovery:
    """A discovered bluetooth device."""

    name: str
    display_name: str
    address: str
    device: BLEDevice


def validate(name: str) -> bool:
    """Validate the name of a Tesla device."""
    return len(name) == 18 and name[0] == "S" and name[17] in "CDRP"


class TeslaBluetoothConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tesla Bluetooth."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_device: Discovery | None = None
        self._discovered_devices: dict[str, Discovery] = {}
        self._interface = TeslaBluetooth()
        self._vehicle: VehicleBluetooth | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle the bluetooth discovery step."""

        # if(SERVICE_UUID not in discovery_info.service_uuids):
        if not validate(discovery_info.name):
            LOGGER.debug(
                "Ignored BT device: %s @ %s",
                discovery_info.name,
                discovery_info.address,
            )
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        display_name = await self._interface.vehicles.query_display_name(
            discovery_info.device, 5
        )

        LOGGER.debug(
            "Ready to setup: %s / %s @ %s",
            discovery_info.name,
            display_name,
            discovery_info.address,
        )

        self.context["title_placeholders"] = {"name": discovery_info.name}
        self._discovered_device = Discovery(
            discovery_info.name,
            display_name or discovery_info.name,
            discovery_info.address,
            discovery_info.device,
        )

        return await self.async_step_vin()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select the vehicle."""

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            self._discovered_device = self._discovered_devices[address]

            self.context["title_placeholders"] = {
                "name": self._discovered_device.name,
            }

            return await self.async_step_vin()

        current_addresses = self._async_current_ids(include_ignore=False)
        for discovery_info in async_discovered_service_info(self.hass):
            if discovery_info.address in current_addresses:
                LOGGER.debug(
                    "Skipping already configured device %s", discovery_info.address
                )
                continue
            if discovery_info.address in self._discovered_devices:
                LOGGER.debug(
                    "Skipping already discovered device %s", discovery_info.address
                )
                continue
            if not validate(discovery_info.name):
                LOGGER.debug("Skipping invalid device name %s", discovery_info.name)
                continue

            # Get display name
            display_name = await self._interface.vehicles.query_display_name(
                discovery_info.device, 5
            )

            self._discovered_devices[discovery_info.address] = Discovery(
                discovery_info.name,
                display_name or discovery_info.name,
                discovery_info.address,
                discovery_info.device,
            )

        titles = {
            address: discovery.name
            for (address, discovery) in self._discovered_devices.items()
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(titles),
                },
            ),
        )

    async def async_step_vin(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Get the vehicles VIN."""
        errors = {}
        assert self._discovered_device
        if user_input is not None:
            vin = user_input[CONF_VIN]
            expected = "S" + hashlib.sha1(vin.encode("utf-8")).hexdigest()[:16]
            if self._discovered_device.name.startswith(expected):
                await self._interface.get_private_key(
                    self.hass.config.path(PRIVATE_KEY_FILE)
                )
                self._vehicle = self._interface.vehicles.createBluetooth(
                    vin=vin,
                    device=self._discovered_device.device,
                )
                await self._vehicle.connect()
                return await self.async_step_check()
            errors["base"] = "invalid_vin"

        return self.async_show_form(
            step_id="vin",
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
        assert self._discovered_device is not None
        assert self._vehicle is not None

        try:
            await self._vehicle.handshakeVehicleSecurity()
        except NotOnWhitelistFault:
            return await self.async_step_instructions()
        except TeslaFleetError as err:
            LOGGER.error("Failed to connect to vehicle: %s", err)
            self.async_abort(reason="unknown_error")

        # Entry will try to connect so lets disconnect first.
        await self._vehicle.disconnect()
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
            # Make this more specific
            except TeslaFleetError as err:
                LOGGER.error("Failed to pair vehicle: %s", err)

        return self.async_show_form(step_id="instructions", errors={"base": "timeout"})

    async def async_step_abort(self, reason: str) -> ConfigFlowResult:
        """Abort the flow."""
        if self._vehicle:
            await self._vehicle.disconnect()
        return self.async_abort(reason=reason)
