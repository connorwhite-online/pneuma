#ifndef PNEUMA_WAKEWORD_H
#define PNEUMA_WAKEWORD_H

#include <stdbool.h>

/* Always-on keyword spotting on the PDM mic. */
void wakeword_init(void);

/* True once when "Hey Pneuma" is detected since the last call. */
bool wakeword_detected(void);

#endif /* PNEUMA_WAKEWORD_H */
