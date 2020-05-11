#ifndef __CSCAN_SCAN_H__
#define __CSCAN_SCAN_H__

#include <inttypes.h>

typedef struct MatchConditions_s {
    uint8_t *data;
    int data_length;
    int alignment;
    int is_float;
    int floor;
} MatchConditions_t;

typedef struct MatchedOffsets_s {
    size_t *matchbuffer;
    size_t size;
} MatchedOffsets_t;

extern MatchedOffsets_t *scan(uint8_t *buffer, size_t size, MatchConditions_t *match);
extern MatchedOffsets_t *filter(uint8_t *buffer, MatchConditions_t *match, MatchedOffsets_t *matches);

#endif