
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <stdio.h>

#include "scan.h"

#define likely(x)      __builtin_expect(!!(x), 1)
#define unlikely(x)    __builtin_expect(!!(x), 0) 
//#define BENCHMARK_SCANNING

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
    const float fvalue = is_float > 1 ? (float) value : *(float *) &(data[0]);
    const double dvalue = is_float > 1 ? (double) value : *(double *) &(data[0]);
    float flow=0.0, fhigh=0.0;
    double dlow=0.0, dhigh=0.0;
    if (is_float) {
        dlow = dvalue - match->precision;
        dhigh = dvalue + match->precision;
        flow = fvalue - match->precision;
        fhigh = fvalue + match->precision;
    }
    #ifdef BENCHMARK_SCANNING
    clock_t scan_time = clock();
    for (int i=0; i<1000; i++) { matchbufferpos = 0;
    #endif
    for (size_t offset=0; offset<last_pos; offset += increment) {
        isMatched = ((
                        (*((uint64_t *) (buffer+offset)) == value) || // if full 64-bit is matched, it's definitely a match
                        (data_length <= 4 && *((uint32_t *) (buffer+offset)) == (uint32_t) value) || // if 32-bits matched and we had <= 32 bits of data
                        (data_length <= 2 && *((uint16_t *) (buffer+offset)) == (uint16_t) value) || // if 16-bits matched and we had <= 16 bits of data
                        (data_length == 1 && *((uint8_t *) (buffer+offset)) == (uint8_t) value) // if 8-bits matched and we had 8 bits of data
                    ) || // if no bits matched, check if we're looking for floats
                    (is_float && data_length == 4 && (
                        flow < *((float *) (buffer+offset)) && fhigh > *((float *) (buffer+offset)) // for floats we do low < value < high search instead of equality
                    )) || 
                    (is_float && data_length == 8 && (
                        dlow < *((double *) (buffer+offset)) && dhigh > *((double *) (buffer+offset))
                    )));

        if (unlikely(isMatched)) {
            matchbuffer[matchbufferpos++] = offset;
        }
    }
    #ifdef BENCHMARK_SCANNING
    }
    scan_time = clock() - scan_time;
    printf("%d-bit %s Scan speed: %.03lf Mb/s\n", 8*match->data_length, match->is_float ? "float" : "int", (double) size * CLOCKS_PER_SEC / (1000 * scan_time));
    #endif
    return trim_matchbuffer(matchbuffer, matchbufferpos);  
}

MatchedOffsets_t *filter(uint8_t *buffer, MatchConditions_t *match, MatchedOffsets_t *matches) {
    int isMatched;
    const int data_length = match->data_length;
    const size_t size = matches->size;
    const int is_float = match->is_float;

    size_t *matchbuffer = malloc(sizeof(size_t) * matches->size) ;
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
    float flow=0.0, fhigh=0.0;
    double dlow=0.0, dhigh=0.0;
    if (match->is_float) {
        dlow = dvalue - match->precision;
        dhigh = dvalue + match->precision;
        flow = fvalue - match->precision;
        fhigh = fvalue + match->precision;
    }

    size_t offset;
    for (size_t i=0; i<size; i++) {
        offset = matches->matchbuffer[i];
        isMatched = ((
                        (*((uint64_t *) (buffer+offset)) == value) ||
                        (data_length <= 4 && *((uint32_t *) (buffer+offset)) == (uint32_t) value) ||
                        (data_length <= 2 && *((uint16_t *) (buffer+offset)) == (uint16_t) value) ||
                        (data_length == 1 && *((uint8_t *) (buffer+offset)) == (uint8_t) value)
                    ) ||
                    (is_float && data_length == 4 && (
                        flow < *((float *) (buffer+offset)) && fhigh > *((float *) (buffer+offset))
                    )) || 
                    (is_float && data_length == 8 && (
                        dlow < *((double *) (buffer+offset)) && dhigh > *((double *) (buffer+offset))
                    )));


        if (unlikely(isMatched)) {
            matchbuffer[matchbufferpos++] = offset;
        }
    }

    return trim_matchbuffer(matchbuffer, matchbufferpos);  
}

void free_matched_offsets(MatchedOffsets_t *data) {
    free(data);
}