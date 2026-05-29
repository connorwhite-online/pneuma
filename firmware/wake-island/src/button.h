#ifndef PNEUMA_BUTTON_H
#define PNEUMA_BUTTON_H

#include <stdbool.h>
#include "pneuma.h"

void button_init(void);

/* If a button gesture occurred, set *reason and return true. */
bool button_event(enum wake_reason *reason);

#endif /* PNEUMA_BUTTON_H */
