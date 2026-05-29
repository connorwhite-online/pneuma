#include "uart_link.h"

/*
 * TODO: implement the line/TLV protocol from docs/PROTOCOL.md over a Zephyr UART
 * device (async or interrupt API):
 *   TX: "WAKE reason=wakeword|button ...", "BATT level=NN"
 *   RX: "READY", "STATE ...", "SLEEP"
 * The island also owns instant UX cues (wake chime / LED) before the SoC boots.
 */

void uart_link_init(void)
{
	/* TODO: get UART device, configure baud, set up RX callback. */
}

void uart_link_send_wake(enum wake_reason reason)
{
	(void)reason;
	/* TODO: format and write the WAKE line. */
}

void uart_link_wait_for_sleep(void)
{
	/* TODO: block (with timeout) until a SLEEP line is received. */
}
