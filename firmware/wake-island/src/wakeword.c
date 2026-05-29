#include "wakeword.h"

/*
 * TODO: wire the PDM mic (nrfx PDM driver) into a small KWS model.
 * Options: a DS-CNN via TFLite-Micro + CMSIS-NN on the nRF52840, or offload to a
 * Syntiant NDP120 front-end (<1 mW) and just read its detect line here.
 * For now this is a stub that never triggers.
 */

void wakeword_init(void)
{
	/* TODO: init PDM, load model, start the inference task. */
}

bool wakeword_detected(void)
{
	/* TODO: return true on a confident "Hey Pneuma" detection. */
	return false;
}
