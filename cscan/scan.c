
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <stdio.h>

#include "scan.h"

#define likely(x)      __builtin_expect(!!(x), 1)
#define unlikely(x)    __builtin_expect(!!(x), 0) 

MatchedOffsets_t *trim_matchbuffer(size_t *matchbuffer, size_t size);

MatchedOffsets_t *trim_matchbuffer(size_t *matchbuffer, size_t size) {
    MatchedOffsets_t *result = malloc(sizeof(MatchedOffsets_t));
    result->size = size;
    if (size > 0) {
        result->matchbuffer = malloc(sizeof(size_t) * size);
        for (size_t pos=0; pos<size; pos++) {
            result->matchbuffer[pos] = matchbuffer[pos];
        }
    }
    free(matchbuffer);
    return result;
}

MatchedOffsets_t *scan(uint8_t *buffer, size_t size, MatchConditions_t *match) {
    int isMatched;
    const int data_length = match->data_length;
    const size_t last_pos = size - data_length;
    const int increment = match->alignment;
    const int is_float = match->is_float;

    size_t *matchbuffer = malloc(sizeof(size_t) * size) ;
    int matchbufferpos = 0;

    uint8_t data[8];
    for (int i=0; i<8; i++) {
        if (i < match->data_length)
            data[i] = match->data[i];
        else
            data[i] = 0;
    }
    const uint64_t value = *(uint64_t *) &(data[0]);
    const float fvalue = *(float *) &(data[0]);
    const double dvalue = *(double *) &(data[0]);
    float flow, fhigh;
    double dlow, dhigh;
    if (match->is_float) {
        dlow = floor(match->data_length == 8 ? dvalue * match->floor : fvalue * match->floor);
        dhigh = dlow + 1.0;
        flow = (float) dlow;
        fhigh = flow + 1.0;
        dlow /= match->floor;
        dhigh /= match->floor;
        flow /= match->floor;
        fhigh /= match->floor;
        printf("Searching for floats between %f and %f\n", flow, fhigh);
    }
    clock_t scan_time = clock();
    for (int i=0; i<1000; i++) { matchbufferpos = 0;
    for (size_t offset=0; offset<last_pos; offset += increment) {
        isMatched = *((uint64_t *) (buffer+offset)) == value || 
                    (is_float && (
                        dlow < *((double *) (buffer+offset)) && dhigh > *((double *) (buffer+offset))
                    )) ||
                    (data_length < 8 && *((uint32_t *) (buffer+offset)) == (uint32_t) value) || 
                    (data_length < 8 && is_float && (
                        flow < *((float *) (buffer+offset)) && fhigh > *((float *) (buffer+offset))
                    )) ||
                    (data_length < 4 && *((uint16_t *) (buffer+offset)) == (uint16_t) value) || 
                    (data_length == 1 && *((uint8_t *) (buffer+offset)) == (uint8_t) value);


        if (unlikely(isMatched)) {
            matchbuffer[matchbufferpos++] = offset;
        }
    }
    }
    scan_time = clock() - scan_time;
    printf("Scan speed: %.03lf Mb/s\n", (double) size * CLOCKS_PER_SEC / (1000 * scan_time));
    return trim_matchbuffer(matchbuffer, matchbufferpos);  
}