# nRF Connect SDK (Zephyr) application for the Pneuma wake island.
# Build with: west build -b nrf52840dk/nrf52840 firmware/wake-island
cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(pneuma_wake_island)

target_sources(app PRIVATE
	src/main.c
	src/wakeword.c
	src/button.c
	src/power.c
	src/uart_link.c
)
