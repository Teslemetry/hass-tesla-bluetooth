"""Sensor platform for Tesla Bluetooth integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from itertools import chain

from tesla_fleet_api.tesla.vehicle.bluetooth import ChargeState

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import TeslaBluetoothConfigEntry
from .models import TeslaBluetoothData

PARALLEL_UPDATES = 0

CHARGE_STATES = {
    "Starting": "starting",
    "Charging": "charging",
    "Stopped": "stopped",
    "Complete": "complete",
    "Disconnected": "disconnected",
    "NoPower": "no_power",
}

SHIFT_STATES = {"P": "p", "D": "d", "R": "r", "N": "n"}


@dataclass(frozen=True, kw_only=True)
class TeslaBluetoothChargeSensorEntityDescription(SensorEntityDescription):
    """Describes Tesla Fleet Sensor entity."""

    value_fn: Callable[[ChargeState], StateType]


CHARGE_DESCRIPTIONS: tuple[TeslaBluetoothChargeSensorEntityDescription, ...] = (
    TeslaBluetoothChargeSensorEntityDescription(
        key="charge_state_charging_state",
        options=list(CHARGE_STATES.values()),
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda x: ChargeState(x.charging_state),
    ),
)


@dataclass(frozen=True, kw_only=True)
class TeslaFleetSensorEntityDescription(SensorEntityDescription):
    """Describes Tesla Fleet Sensor entity."""

    value_fn: Callable[[ChargeState], StateType]


VEHICLE_DESCRIPTIONS: tuple[TeslaFleetSensorEntityDescription, ...] = (
    TeslaFleetSensorEntityDescription(
        key="charge_state_battery_level",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
    ),
    TeslaFleetSensorEntityDescription(
        key="charge_state_usable_battery_level",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="charge_state_charge_energy_added",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        suggested_display_precision=1,
    ),
    TeslaFleetSensorEntityDescription(
        key="charge_state_charger_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
    ),
    TeslaFleetSensorEntityDescription(
        key="charge_state_charger_voltage",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslaFleetSensorEntityDescription(
        key="charge_state_charger_actual_current",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslaFleetSensorEntityDescription(
        key="charge_state_charge_rate",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TeslaFleetSensorEntityDescription(
        key="charge_state_conn_charge_cable",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="charge_state_fast_charger_type",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="charge_state_battery_range",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=1,
    ),
    TeslaFleetSensorEntityDescription(
        key="charge_state_est_battery_range",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="charge_state_ideal_battery_range",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="drive_state_speed",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.MILES_PER_HOUR,
        device_class=SensorDeviceClass.SPEED,
        entity_registry_enabled_default=False,
        value_fn=lambda value: value or 0,
    ),
    TeslaFleetSensorEntityDescription(
        key="drive_state_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda value: value or 0,
    ),
    TeslaFleetSensorEntityDescription(
        key="drive_state_shift_state",
        options=list(SHIFT_STATES.values()),
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda x: SHIFT_STATES.get(str(x), "p"),
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="vehicle_state_odometer",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="vehicle_state_tpms_pressure_fl",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        suggested_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="vehicle_state_tpms_pressure_fr",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        suggested_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="vehicle_state_tpms_pressure_rl",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        suggested_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="vehicle_state_tpms_pressure_rr",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        suggested_unit_of_measurement=UnitOfPressure.PSI,
        device_class=SensorDeviceClass.PRESSURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="climate_state_inside_temp",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=1,
    ),
    TeslaFleetSensorEntityDescription(
        key="climate_state_outside_temp",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=1,
    ),
    TeslaFleetSensorEntityDescription(
        key="climate_state_driver_temp_setting",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="climate_state_passenger_temp_setting",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="drive_state_active_route_traffic_minutes_delay",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="drive_state_active_route_energy_at_arrival",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    TeslaFleetSensorEntityDescription(
        key="drive_state_active_route_miles_to_arrival",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.MILES,
        device_class=SensorDeviceClass.DISTANCE,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TeslaBluetoothConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Tesla Fleet sensor platform from a config entry."""
    async_add_entities(
        chain(
            (
                TeslaBluetoothStateSensorEntity(entry.runtime_data, description)
                for description in STATE_DESCRIPTIONS
            ),
        )
    )


class TeslaBluetoothSensorBase(TeslaBluetoothEntity, SensorEntity):
    """Base class for Tesla Bluetooth sensors."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        data: TeslaBluetoothData,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self.entity_description = description
        super().__init__(data, description.key)

    def _async_update_attrs(self) -> None:
        """Update the attributes of the sensor."""
        self._attr_native_value = self.entity_description.value_fn(
            self.coordinator.data
        )


class TeslaBluetoothChargeSensor(TeslaBluetoothChargeEntity, TeslaBluetoothSensorBase):
    """Base class for Tesla Bluetooth charge sensors."""

    entity_description: TeslaBluetoothChargeSensorEntityDescription
