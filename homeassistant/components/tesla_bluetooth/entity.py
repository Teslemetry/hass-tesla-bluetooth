"""Tesla Bluetooth parent entity class."""

from abc import abstractmethod
from typing import Generic, TypeVar

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER
from .coordinator import TeslaBluetoothCoordinator, TeslaBluetoothStateCoordinator
from .models import TeslaBluetoothData

_C = TypeVar("_C", bound=TeslaBluetoothCoordinator)


class TeslaBluetoothEntity(CoordinatorEntity[_C], Generic[_C]):
    """Parent class for all Tesla Bluetooth entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        data: TeslaBluetoothData,
        coordinator: _C,
        key: str,
    ) -> None:
        """Initialize common aspects of a TeslaFleet entity."""
        super().__init__(coordinator)
        self.vehicle = data.vehicle
        self.coordinators = data.coordinators
        self._attr_translation_key = key
        self._attr_unique_id = f"{data.vehicle.vin}-{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, data.vehicle.vin)},
            manufacturer="Tesla",
            model=data.vehicle.model,
            name=data.vehicle.vin,
            serial_number=data.vehicle.vin,
        )

    @property
    def available(self) -> bool:
        """Return if sensor is available."""
        return self.vehicle.client.is_connected

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data is not None:
            self._async_update_attrs()
        self.async_write_ha_state()

    @abstractmethod
    def _async_update_attrs(self) -> None:
        """Update the attributes of the entity."""

    @property
    def awake(self) -> bool:
        """Return if the vehicle is asleep."""
        return (
            self.coordinators.state.data.vehicleSleepStatus == 1
        )  # VEHICLE_SLEEP_STATUS_AWAKE

    async def wake_up_if_asleep(self) -> None:
        """Wake up the vehicle if it is asleep."""
        if self.awake:
            result = await self.vehicle.wake_up()
            LOGGER.debug("Wake up result: %s", result)


class TeslaBluetoothStateEntity(TeslaBluetoothEntity[TeslaBluetoothStateCoordinator]):
    """Entity class for Tesla Bluetooth State entities."""

    kind = "state"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a TeslaFleet entity."""
        super().__init__(data, data.coordinators.state, key)


class TeslaBluetoothChargeEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Charge entities."""

    kind = "charge"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.charge, key)


class TeslaBluetoothClimateEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Climate entities."""

    kind = "climate"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.climate, key)


class TeslaBluetoothClosuresEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Closures entities."""

    kind = "closures"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.closures, key)


class TeslaBluetoothDriveEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Drive entities."""

    kind = "drive"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.drive, key)


class TeslaBluetoothLocationEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Location entities."""

    kind = "location"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.location, key)


class TeslaBluetoothChargeScheduleEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Charge Schedule entities."""

    kind = "charge_schedule"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.charge_schedule, key)


class TeslaBluetoothPreconditioningScheduleEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Preconditioning Schedule entities."""

    kind = "preconditioning_schedule"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.preconditioning_schedule, key)


class TeslaBluetoothTirePressureEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Tire Pressure entities."""

    kind = "tire_pressure"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.tire_pressure, key)


class TeslaBluetoothMediaEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Media entities."""

    kind = "media"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.media, key)


class TeslaBluetoothMediaDetailEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Media Detail entities."""

    kind = "media_detail"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.media_detail, key)


class TeslaBluetoothSoftwareUpdateEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Software Update entities."""

    kind = "software_update"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.software_update, key)


class TeslaBluetoothParentalControlsEntity(TeslaBluetoothEntity):
    """Entity class for Tesla Bluetooth Parental Controls entities."""

    kind = "parental_controls"

    def __init__(self, data: TeslaBluetoothData, key: str) -> None:
        """Initialize common aspects of a Tesla Bluetooth entity."""
        super().__init__(data, data.coordinators.parental_controls, key)
