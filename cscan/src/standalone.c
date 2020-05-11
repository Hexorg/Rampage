#include "ptrace/process.h"
#include "scan.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int pid = atoi(argv[1]);
    Process_t* process = Process_new(pid);
    uint8_t *data = Process_get_bytes(process, (void *)0x7ffbfffdd000, 135168);

    int value = 12;
    MatchConditions_t match;
    match.data = (uint8_t *)&value;
    match.data_length = 4;
    match.alignment = 1;
    match.is_float = 0;
    match.floor = 0;
    MatchedOffsets_t *result = scan(data, 135168, &match);
    printf("Found %ld matches\n", result->size);
    for (size_t i=0; i<result->size; i++) {
        printf("\t0x%lx\n", result->matchbuffer[i]+0x7ffbfffdd000);
    }

    // printf("Read value is %d\n", value);
    Process_free(&process);
    return 0;
}