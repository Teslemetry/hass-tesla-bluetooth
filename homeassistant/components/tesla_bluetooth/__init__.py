"""Tesla Bluetooth integration."""

from typing import Final

from bleak.exc import BleakError
from bleak_retry_connector import close_stale_connections_by_address
from tesla_fleet_api.tesla.bluetooth import TeslaBluetooth
from tesla_fleet_api.tesla.vehicle.vehicles import VehicleBluetooth

from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
    async_get_scanner,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, LOGGER, PRIVATE_KEY_FILE
from .coordinator import TesleBluetoothCoordinators
from .models import TeslaBluetoothData

type TeslaBluetoothConfigEntry = ConfigEntry[TeslaBluetoothData]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
PLATFORMS: Final = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SWITCH,
]  # Platform.SENSOR


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Tesla Bluetooth integration."""

    parent = TeslaBluetooth()
    await parent.get_private_key(hass.config.path(PRIVATE_KEY_FILE))
    hass.data[DOMAIN] = parent
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: TeslaBluetoothConfigEntry
) -> bool:
    """Set up the Tesla Bluetooth configuration."""

    parent: TeslaBluetooth = hass.data[DOMAIN]
    vehicle: VehicleBluetooth = parent.vehicles.createBluetooth(entry.data["vin"])

    address = entry.data["address"]
    await close_stale_connections_by_address(address)

    ble_device = async_ble_device_from_address(hass, address, True)
    if not ble_device:
        LOGGER.warning(
            "Could not find Tesla vehicle with address %s, running scan.", address
        )
        # Do an active scan to find the device
        ble_device = await async_get_scanner(hass).find_device_by_address(address)
    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find Tesla vehicle with address {address}"
        )
    vehicle.set_device(ble_device)

    try:
        await vehicle.connect(max_attempts=10)
    except BleakError as e:
        raise ConfigEntryNotReady(f"Failed to connect to Tesla vehicle: {e}") from e

    coordinators = TesleBluetoothCoordinators(hass, entry, vehicle)
    await coordinators.state.async_config_entry_first_refresh()
    # Force the state coordinator to update even without entities
    coordinators.state.async_add_listener(lambda *_: None)

    # Wake up the vehicle if it is asleep
    if coordinators.state.data.vehicleSleepStatus != 1:
        try:
            await vehicle.wake_up()
        except TimeoutError:
            LOGGER.warning("Failed to wake up Tesla vehicle")

    entry.runtime_data = TeslaBluetoothData(vehicle, coordinators)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: TeslaBluetoothConfigEntry
) -> bool:
    """Unload TeslaFleet Config."""
    await entry.runtime_data.vehicle.disconnect()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
