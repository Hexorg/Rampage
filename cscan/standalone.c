#include "ptrace/process.h"
#include "scan.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int pid = atoi(argv[1]);
    Process_t* process = Process_new(pid);
    char *data = Process_get_bytes(process, (void *)0x7efbff50e000, 1318912);

    double value = 80085.235f;
    MatchConditions_t match;
    match.data = (uint8_t *)&value;
    match.data_length = 8;
    match.alignment = 1;
    match.is_float = 0;
    match.floor = 100;
    scan(data, 1318912, &match);

    // printf("Read value is %d\n", value);
    Process_free(&process);
    return 0;
}