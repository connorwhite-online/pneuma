/*
 * Pneuma wake-island firmware (nRF52840, Zephyr / nRF Connect SDK).
 *
 * Always-on co-processor: listen for the wake word / button, power up the Linux
 * session SoC on demand, hand off over UART, then power it back down. This is
 * what keeps the power- and heat-hungry tier off ~99% of the time
 * (see docs/ARCHITECTURE.md §1 and docs/PROTOCOL.md).
 *
 * STATUS: scaffold. Builds against the nRF Connect SDK toolchain (not part of
 * this repo's CI). Module bodies are stubs marked TODO.
 */
#include <zephyr/kernel.h>

#include "pneuma.h"
#include "wakeword.h"
#include "button.h"
#include "power.h"
#include "uart_link.h"

int main(void)
{
	wakeword_init();
	button_init();
	power_init();
	uart_link_init();

	for (;;) {
		enum wake_reason reason = WAKE_NONE;

		if (wakeword_detected()) {
			reason = WAKE_WORD;
		} else {
			button_event(&reason); /* sets reason if a button fired */
		}

		if (reason != WAKE_NONE) {
			power_soc_on();              /* assert SOC_EN -> boot session tier */
			uart_link_send_wake(reason); /* tell the SoC why we woke */
			uart_link_wait_for_sleep();  /* block until the SoC says SLEEP */
			power_soc_off();             /* cut the session tier */
		}

		/* TODO: replace polling with IRQ/event-driven low-power idle so the
		 * island truly sips µA between wakes. */
		k_msleep(10);
	}

	return 0;
}
