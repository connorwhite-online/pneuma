#include "button.h"

/*
 * TODO: configure the button GPIO with an interrupt (Zephyr gpio + gpio_callback)
 * and classify tap / double-tap / long-press, mapping to WAKE_BUTTON_TAP,
 * WAKE_VISUAL (e.g. long-press = "look at this"), WAKE_BUTTON_LONG.
 */

void button_init(void)
{
	/* TODO: gpio_pin_configure_dt + interrupt callback. */
}

bool button_event(enum wake_reason *reason)
{
	(void)reason;
	/* TODO: drain the gesture queue; set *reason and return true if one fired. */
	return false;
}
