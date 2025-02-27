"""The Tesla Bluetooth coordinator."""

from __future__ import annotations

from abc import abstractmethod
from datetime import timedelta
from typing import TYPE_CHECKING, Generic, TypeVar

from tesla_fleet_api.tesla.bluetooth import toDict
from tesla_fleet_api.tesla.vehicle.bluetooth import (
    ChargeScheduleState,
    ChargeState,
    ClimateState,
    ClosuresState,
    DriveState,
    LocationState,
    MediaDetailState,
    MediaState,
    ParentalControlsState,
    PreconditioningScheduleState,
    SoftwareUpdateState,
    TirePressureState,
    VehicleBluetooth,
    VehicleStatus,
)

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator,
    UpdateFailed,
)

from .const import DEFAULT_SCAN_INTERVAL, LOGGER

if TYPE_CHECKING:
    from . import TeslaBluetoothConfigEntry

_T = TypeVar("_T")


class TesleBluetoothCoordinators:
    """Data class for Tesla Bluetooth coordinators."""

    state: TeslaBluetoothStateCoordinator
    charge: TeslaBluetoothChargeCoordinator
    climate: TeslaBluetoothClimateCoordinator
    closures: TeslaBluetoothClosuresCoordinator
    drive: TeslaBluetoothDriveCoordinator
    location: TeslaBluetoothLocationCoordinator
    charge_schedule: TeslaBluetoothChargeScheduleCoordinator
    preconditioning_schedule: TeslaBluetoothPreconditioningScheduleCoordinator
    tire_pressure: TeslaBluetoothTirePressureCoordinator
    media: TeslaBluetoothMediaCoordinator
    media_detail: TeslaBluetoothMediaDetailCoordinator
    software_update: TeslaBluetoothSoftwareUpdateCoordinator
    parental_controls: TeslaBluetoothParentalControlsCoordinator

    def __init__(
        self,
        hass: HomeAssistant,
        entry: TeslaBluetoothConfigEntry,
        vehicle: VehicleBluetooth,
    ) -> None:
        """Initialize all coordinators."""
        self.state = TeslaBluetoothStateCoordinator(hass, entry, vehicle, self)
        self.charge = TeslaBluetoothChargeCoordinator(hass, entry, vehicle, self)
        self.climate = TeslaBluetoothClimateCoordinator(hass, entry, vehicle, self)
        self.closures = TeslaBluetoothClosuresCoordinator(hass, entry, vehicle, self)
        self.drive = TeslaBluetoothDriveCoordinator(hass, entry, vehicle, self)
        self.location = TeslaBluetoothLocationCoordinator(hass, entry, vehicle, self)
        self.charge_schedule = TeslaBluetoothChargeScheduleCoordinator(
            hass, entry, vehicle, self
        )
        self.preconditioning_schedule = (
            TeslaBluetoothPreconditioningScheduleCoordinator(hass, entry, vehicle, self)
        )
        self.tire_pressure = TeslaBluetoothTirePressureCoordinator(
            hass, entry, vehicle, self
        )
        self.media = TeslaBluetoothMediaCoordinator(hass, entry, vehicle, self)
        self.media_detail = TeslaBluetoothMediaDetailCoordinator(
            hass, entry, vehicle, self
        )
        self.software_update = TeslaBluetoothSoftwareUpdateCoordinator(
            hass, entry, vehicle, self
        )
        self.parental_controls = TeslaBluetoothParentalControlsCoordinator(
            hass, entry, vehicle, self
        )

    def __iter__(self):
        """Iterate through coordinators."""
        for attr_name in self.__annotations__:
            yield getattr(self, attr_name)


class TeslaBluetoothCoordinator(TimestampDataUpdateCoordinator[_T], Generic[_T]):
    """Class to manage fetching Tesla Bluetooth data."""

    vehicle: VehicleBluetooth
    need_awake: bool = True
    kind: str

    def __init__(
        self,
        hass: HomeAssistant,
        entry: TeslaBluetoothConfigEntry,
        vehicle: VehicleBluetooth,
        coordinators: TesleBluetoothCoordinators,
    ) -> None:
        """Initialize the coordinator."""
        self.vehicle = vehicle
        self.coordinators = coordinators
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"Tesla Bluetooth {self.kind} Coordinator",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> _T:
        """Get data from Tesla Bluetooth."""
        LOGGER.info(
            f"Updating {self.kind} data. Connected: {self.vehicle.client.is_connected}"
        )

        if not self.vehicle.client.is_connected:
            await self.vehicle.connect()
            # raise UpdateFailed("Disconnected")
        if (
            self.need_awake
            and self.coordinators.state.data is not None
            and self.coordinators.state.data.vehicleSleepStatus != 1
        ):
            raise UpdateFailed("Vehicle is sleeping")
        try:
            data = await self._async_update_function(self.vehicle)
        except Exception as err:
            raise UpdateFailed(f"Unable to fetch data: {err}") from err
        if data:
            LOGGER.info(f"Updated {self.kind} data {toDict(data)}")
        return data

    @abstractmethod
    async def _async_update_function(self, vehicle: VehicleBluetooth) -> _T:
        """Abstract method to fetch specific data from the vehicle."""


class TeslaBluetoothStateCoordinator(TeslaBluetoothCoordinator[VehicleStatus]):
    """Coordinator for Tesla vehicle state data."""

    need_awake = False
    kind = "State"

    async def _async_update_function(self, vehicle: VehicleBluetooth) -> VehicleStatus:
        """Get vehicle state data."""
        return await vehicle.vehicle_state()


class TeslaBluetoothChargeCoordinator(TeslaBluetoothCoordinator[ChargeState]):
    """Coordinator for Tesla charge state data."""

    kind = "Charge"

    async def _async_update_function(self, vehicle: VehicleBluetooth) -> ChargeState:
        """Get vehicle charge state data."""
        return await vehicle.charge_state()


class TeslaBluetoothClimateCoordinator(TeslaBluetoothCoordinator[ClimateState]):
    """Coordinator for Tesla climate state data."""

    kind = "Climate"

    async def _async_update_function(self, vehicle: VehicleBluetooth) -> ClimateState:
        """Get vehicle climate state data."""
        return await vehicle.climate_state()


class TeslaBluetoothDriveCoordinator(TeslaBluetoothCoordinator[DriveState]):
    """Coordinator for Tesla drive state data."""

    kind = "Drive"

    async def _async_update_function(self, vehicle: VehicleBluetooth) -> DriveState:
        """Get vehicle drive state data."""
        return await vehicle.drive_state()


class TeslaBluetoothLocationCoordinator(TeslaBluetoothCoordinator[LocationState]):
    """Coordinator for Tesla location state data."""

    kind = "Location"

    async def _async_update_function(self, vehicle: VehicleBluetooth) -> LocationState:
        """Get vehicle location state data."""
        return await vehicle.location_state()


class TeslaBluetoothClosuresCoordinator(TeslaBluetoothCoordinator[ClosuresState]):
    """Coordinator for Tesla closures state data."""

    kind = "Closures"

    async def _async_update_function(self, vehicle: VehicleBluetooth) -> ClosuresState:
        """Get vehicle closures state data."""
        return await vehicle.closures_state()


class TeslaBluetoothChargeScheduleCoordinator(
    TeslaBluetoothCoordinator[ChargeScheduleState]
):
    """Coordinator for Tesla charge schedule state data."""

    kind = "Charge Schedule"

    async def _async_update_function(
        self, vehicle: VehicleBluetooth
    ) -> ChargeScheduleState:
        """Get vehicle charge schedule state data."""
        return await vehicle.charge_schedule_state()


class TeslaBluetoothPreconditioningScheduleCoordinator(
    TeslaBluetoothCoordinator[PreconditioningScheduleState]
):
    """Coordinator for Tesla preconditioning schedule state data."""

    kind = "Preconditioning Schedule"

    async def _async_update_function(
        self, vehicle: VehicleBluetooth
    ) -> PreconditioningScheduleState:
        """Get vehicle preconditioning schedule state data."""
        return await vehicle.preconditioning_schedule_state()


class TeslaBluetoothTirePressureCoordinator(
    TeslaBluetoothCoordinator[TirePressureState]
):
    """Coordinator for Tesla tire pressure state data."""

    kind = "Tire Pressure"

    async def _async_update_function(
        self, vehicle: VehicleBluetooth
    ) -> TirePressureState:
        """Get vehicle tire pressure state data."""
        return await vehicle.tire_pressure_state()


class TeslaBluetoothMediaCoordinator(TeslaBluetoothCoordinator[MediaState]):
    """Coordinator for Tesla media state data."""

    kind = "Media"

    async def _async_update_function(self, vehicle: VehicleBluetooth) -> MediaState:
        """Get vehicle media state data."""
        return await vehicle.media_state()


class TeslaBluetoothMediaDetailCoordinator(TeslaBluetoothCoordinator[MediaDetailState]):
    """Coordinator for Tesla media detail state data."""

    kind = "Media Detail"

    async def _async_update_function(
        self, vehicle: VehicleBluetooth
    ) -> MediaDetailState:
        """Get vehicle media detail state data."""
        return await vehicle.media_detail_state()


class TeslaBluetoothSoftwareUpdateCoordinator(
    TeslaBluetoothCoordinator[SoftwareUpdateState]
):
    """Coordinator for Tesla software update state data."""

    kind = "Software Update"

    async def _async_update_function(
        self, vehicle: VehicleBluetooth
    ) -> SoftwareUpdateState:
        """Get vehicle software update state data."""
        return await vehicle.software_update_state()


class TeslaBluetoothParentalControlsCoordinator(
    TeslaBluetoothCoordinator[ParentalControlsState]
):
    """Coordinator for Tesla parental controls state data."""

    kind = "Parental Controls"

    async def _async_update_function(
        self, vehicle: VehicleBluetooth
    ) -> ParentalControlsState:
        """Get vehicle parental controls state data."""
        return await vehicle.parental_controls_state()
