/*
 * Shared types for the Pneuma wake-island firmware.
 */
#ifndef PNEUMA_H
#define PNEUMA_H

/* Why the device woke. Mirrors crate::hal::WakeReason on the session side and
 * the WAKE message in docs/PROTOCOL.md. */
enum wake_reason {
	WAKE_NONE = 0,
	WAKE_WORD,
	WAKE_BUTTON_TAP,
	WAKE_BUTTON_LONG,
	WAKE_VISUAL,
};

#endif /* PNEUMA_H */
