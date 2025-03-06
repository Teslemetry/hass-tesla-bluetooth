"""Switch platform for Tesla Fleet integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from itertools import chain
from typing import Any

from tesla_fleet_api.const import Seat
from tesla_fleet_api.tesla.vehicle.bluetooth import ChargeState, ClimateState

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TeslaBluetoothConfigEntry
from .entity import TeslaBluetoothChargeEntity, TeslaBluetoothClimateEntity
from .helpers import handle_vehicle_command
from .models import TeslaBluetoothData

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class TeslaBluetoothSwitchEntityDescription(SwitchEntityDescription):
    """Describes TeslaBluetooth Switch entity."""

    on_func: Callable
    off_func: Callable


@dataclass(frozen=True, kw_only=True)
class TeslaBluetoothChargeSwitchEntityDescription(
    TeslaBluetoothSwitchEntityDescription
):
    """Describes TeslaBluetooth Switch entity."""

    value_func: Callable[[ChargeState], bool] = bool


@dataclass(frozen=True, kw_only=True)
class TeslaBluetoothClimateSwitchEntityDescription(
    TeslaBluetoothSwitchEntityDescription
):
    """Describes TeslaBluetooth Switch entity."""

    value_func: Callable[[ClimateState], bool] = bool


CLIMATE_DESCRIPTIONS: tuple[TeslaBluetoothClimateSwitchEntityDescription, ...] = (
    TeslaBluetoothClimateSwitchEntityDescription(
        key="climate_state_auto_seat_climate_left",
        on_func=lambda api: api.remote_auto_seat_climate_request(Seat.FRONT_LEFT, True),
        off_func=lambda api: api.remote_auto_seat_climate_request(
            Seat.FRONT_LEFT, False
        ),
        value_func=lambda state: state.auto_seat_climate_left,
    ),
    TeslaBluetoothClimateSwitchEntityDescription(
        key="climate_state_auto_seat_climate_right",
        on_func=lambda api: api.remote_auto_seat_climate_request(
            Seat.FRONT_RIGHT, True
        ),
        off_func=lambda api: api.remote_auto_seat_climate_request(
            Seat.FRONT_RIGHT, False
        ),
        value_func=lambda state: state.auto_seat_climate_right,
    ),
    TeslaBluetoothClimateSwitchEntityDescription(
        key="climate_state_auto_steering_wheel_heat",
        on_func=lambda api: api.remote_auto_steering_wheel_heat_climate_request(
            on=True
        ),
        off_func=lambda api: api.remote_auto_steering_wheel_heat_climate_request(
            on=False
        ),
        value_func=lambda state: state.auto_steering_wheel_heat,
    ),
    TeslaBluetoothClimateSwitchEntityDescription(
        key="climate_state_defrost_mode",
        on_func=lambda api: api.set_preconditioning_max(on=True, manual_override=False),
        off_func=lambda api: api.set_preconditioning_max(
            on=False, manual_override=False
        ),
        value_func=lambda state: state.defrost_mode != "Off",
    ),
)
CHARGE_DESCRIPTIONS: tuple[TeslaBluetoothChargeSwitchEntityDescription, ...] = (
    TeslaBluetoothChargeSwitchEntityDescription(
        key="charge_state_charging_state",
        on_func=lambda api: api.charge_start(),
        off_func=lambda api: api.charge_stop(),
        value_func=lambda state: str(state.charging_state) in {"Starting", "Charging"},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeslaBluetoothConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the TeslaBluetooth Switch platform from a config entry."""

    async_add_entities(
        chain(
            (
                TeslaBluetoothClimateSwitchEntity(entry.runtime_data, description)
                for description in CLIMATE_DESCRIPTIONS
            ),
            (
                TeslaBluetoothChargeSwitchEntity(entry.runtime_data, description)
                for description in CHARGE_DESCRIPTIONS
            ),
        )
    )


class TeslaBluetoothClimateSwitchEntity(TeslaBluetoothClimateEntity, SwitchEntity):
    """Tesla Bluetooth climate switch entities."""

    _attr_device_class = SwitchDeviceClass.SWITCH
    entity_description: TeslaBluetoothClimateSwitchEntityDescription

    def __init__(
        self,
        data: TeslaBluetoothData,
        description: TeslaBluetoothClimateSwitchEntityDescription,
    ) -> None:
        """Initialize the Switch."""
        self.entity_description = description
        super().__init__(data, description.key)

    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""

        self._attr_is_on = self.entity_description.value_func(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the Switch."""
        await self.wake_up_if_asleep()
        await handle_vehicle_command(self.entity_description.on_func(self.vehicle))
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the Switch."""
        await self.wake_up_if_asleep()
        await handle_vehicle_command(self.entity_description.off_func(self.vehicle))
        self._attr_is_on = False
        self.async_write_ha_state()


class TeslaBluetoothChargeSwitchEntity(TeslaBluetoothChargeEntity, SwitchEntity):
    """Tesla Bluetooth charge switch entities."""

    _attr_device_class = SwitchDeviceClass.SWITCH
    entity_description: TeslaBluetoothChargeSwitchEntityDescription

    def __init__(
        self,
        data: TeslaBluetoothData,
        description: TeslaBluetoothChargeSwitchEntityDescription,
    ) -> None:
        """Initialize the Switch."""
        self.entity_description = description
        super().__init__(data, description.key)

    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        self._attr_is_on = self.entity_description.value_func(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the Switch."""
        await self.wake_up_if_asleep()
        await handle_vehicle_command(self.entity_description.on_func(self.vehicle))
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the Switch."""
        await self.wake_up_if_asleep()
        await handle_vehicle_command(self.entity_description.off_func(self.vehicle))
        self._attr_is_on = False
        self.async_write_ha_state()
