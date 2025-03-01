# Tesla Bluetooth

Home Assistant integration for communicating with Tesla vehicles over BLE

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Teslemetry&repository=hass-tesla-bluetooth)

## Limitations

- This will not work with legacy (pre-2021) Model S and Model X vehicles.
- This will not work if the Tesla Fleet, Tessie, or Teslemetry (core version) integrations are configured.
- It will only work with the latest Teslemetry Custom (HACS version) integration, but both need to be kept up to date to ensure library compatibility.
- This is a work in progress, lower your expectations.

## Known Issues

Initial setup may fail after the virtual key is installed. Simply retry the setup and the pairing step will be skipped.
