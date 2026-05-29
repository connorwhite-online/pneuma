#ifndef PNEUMA_POWER_H
#define PNEUMA_POWER_H

void power_init(void);

/* Assert SOC_EN: boot/resume the Linux session SoC + permit modem power. */
void power_soc_on(void);

/* Deassert SOC_EN: cut the session tier (call only after the SoC acks SLEEP). */
void power_soc_off(void);

#endif /* PNEUMA_POWER_H */
