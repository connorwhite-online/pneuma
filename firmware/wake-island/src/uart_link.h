#ifndef PNEUMA_UART_LINK_H
#define PNEUMA_UART_LINK_H

#include "pneuma.h"

/* Control link to the session SoC (see docs/PROTOCOL.md). */
void uart_link_init(void);

/* Send "WAKE reason=..." to the SoC. */
void uart_link_send_wake(enum wake_reason reason);

/* Block until the SoC sends "SLEEP". */
void uart_link_wait_for_sleep(void);

#endif /* PNEUMA_UART_LINK_H */
