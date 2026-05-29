#include "power.h"

/*
 * TODO: drive the SOC_EN GPIO into the PMIC / load switch that gates the session
 * tier. Add sequencing/debounce so the SoC boots cleanly and is only cut after
 * it has acked SLEEP over the UART link.
 */

void power_init(void)
{
	/* TODO: configure SOC_EN GPIO as output, default low (session tier off). */
}

void power_soc_on(void)
{
	/* TODO: set SOC_EN high. */
}

void power_soc_off(void)
{
	/* TODO: set SOC_EN low. */
}
