#include <stdlib.h>
#include <stdio.h>

#include <sys/ptrace.h>
#include <sys/wait.h>
#include <bits/waitflags.h>
#include <signal.h>
#include <string.h>
#include <errno.h>
#include <time.h>

#include "process.h"

//#define READ_WITH_PTRACE

#define unlikely(x)    __builtin_expect(!!(x), 0)
#define WAIT_FOR_SIGNAL(process, signal) do { int status; do { status=Process_wait((process), 1); } while (!WIFSTOPPED(status) && !(WSTOPSIG(status) & (signal))); } while(0)

void onStatusChange(Process_t *process, int status);
uint8_t *readMemFile(Process_t *process, void *address, size_t size);
uint8_t *readWithPtrace(Process_t *process, void *address, size_t size);
void benchmarkMemFileVSPtrace(Process_t *process, void *address, size_t size);


void onStatusChange(Process_t *process, int status) {
    if (WIFEXITED(status)) {
        // Process exited
        int exit_status = WEXITSTATUS(status);
        printf("Process %d exited with status %d\n", process->pid, exit_status);
        process->flags = EXITED;
        exit(0);
    }
    if (WIFSIGNALED(status)) {
        // Process received a signal
        int signal = WTERMSIG(status);
        printf("Process %d received a signal %d: %s\n", process->pid, signal, strsignal(signal));
        #ifdef WCOREDUMP
            if (WCOREDUMP(status)) {
                // Process crashed
                printf("Process %d crashed\n", process->pid);
            }
        #endif
    }
    if (WIFSTOPPED(status)) {
        // Process stopped because of a signal
        int signal = WSTOPSIG(status);
        printf("Process %d stopped with a signal %d: %s\n", process->pid, signal, strsignal(signal));
        SETSTOPPED(process);
    }
}

uint8_t *readMemFile(Process_t *process, void *address, size_t size) {
    uint8_t *buffer = malloc(size);
    if (fseek(process->mem, (long int) address, SEEK_SET) != 0) {
        printf("%s:%d %s(): Faliure while reading %d's memory", __FILE__, __LINE__, __func__, process->pid);
        if (ferror(process->mem)) {
            printf(": error\n");
        } else {
            printf("\n");
        }
    }
    if (fread(buffer, size, 1, process->mem) != 1) {
        printf("%s:%d %s() Couldn't read the whole %ld bytes\n", __FILE__, __LINE__, __func__, size);
    }
    return buffer;
}

uint8_t *readWithPtrace(Process_t *process, void *address, size_t size) {
    uint8_t *buffer = malloc(size);
    const int word_len = sizeof(void *);
    long result = 0;
    size_t offset = 0;
    if (size > word_len) {
        for (offset=0; offset<size; offset+=word_len) {
            result = ptrace(PTRACE_PEEKTEXT, process->pid, address+offset, 0);
            *((long *) (buffer+offset)) = result;
            if (unlikely(result == -1 && errno)) {
                break;
            }
        }
    }

    if (offset < size && result != -1) { // one last chunk that's less than word size is left
        int result_byte = 0;
        result = ptrace(PTRACE_PEEKTEXT, process->pid, address+offset, 0);
        if (result > 0) {
            for (; offset<size; offset++, result_byte++) {
                buffer[offset] = ((uint8_t *)(&result))[result_byte];
            }
        }
    }

    if (result < 0) {
        printf("%s:%d %s(): ptrace error %d: %s\n", __FILE__, __LINE__, __func__, errno, strerror(errno));
    }

    return buffer;
}

void benchmarkMemFileVSPtrace(Process_t *process, void *address, size_t size) {
    clock_t memfile_clock = clock();
    const int iterations = 1000;
    for (int i=0; i<iterations; i++) {
        free(readMemFile(process, address, size));
    }
    memfile_clock = clock() - memfile_clock;
    clock_t ptrace_clock = clock();
    for (int i=0; i<iterations; i++) {
        free(readWithPtrace(process, address, size));
    }
    ptrace_clock = clock() - ptrace_clock;
    printf("Reading %ld bytes took:\n\t%ld clocks (%fs) - with mem file\n\t%ld clocks (%fs) - with ptrace\n", size*iterations, memfile_clock, (float) memfile_clock / CLOCKS_PER_SEC, ptrace_clock, (float) ptrace_clock / CLOCKS_PER_SEC);
    /* Reading 1.318912 GB took:
     *   109401 clocks (0.109401s) - with mem file
     *   30597448 clocks (30.597448s) - with ptrace
    */
}

Process_t *Process_new(int pid) {
    Process_t *result = malloc(sizeof(Process_t));
    result->pid = pid;
    result->flags = 0;
    SETRUNNING(result);
    Process_attach(result);
    char path[64];
    sprintf(path, "/proc/%d/mem", pid);
    result->mem = fopen(path, "rb");
    return result;
}

void Process_attach(Process_t *process) {
    if (ISATTACHED(process)) {
        return;
    }
    int result = ptrace(PTRACE_ATTACH, process->pid, 0, 0);
    
    if (result == -1) {
        printf("%s:%d %s(): ptrace error %d: %s\n", __FILE__, __LINE__, __func__, errno, strerror(errno));
    }

    WAIT_FOR_SIGNAL(process, SIGTRAP | SIGSTOP);
    SETATTACHED(process);
}

void Process_detach(Process_t *process) {
    int result = ptrace(PTRACE_DETACH, process->pid, 0, 0);
    if (result == -1) {
        printf("%s:%d %s(): ptrace error %d: %s\n", __FILE__, __LINE__, __func__, errno, strerror(errno));
    }
}

int Process_wait(Process_t *process, int is_blocking) {
    int options = 0;
    if (!is_blocking) {
        options |= WNOHANG;
    }
    int status;
    pid_t r = waitpid(process->pid, &status, options);
    if (r != process->pid && is_blocking) {
        printf("%s:%d %s(): waitpid error %d: %s\n", __FILE__, __LINE__, __func__, errno, strerror(errno));
    }
    onStatusChange(process, status);
    return status;
}

void Process_stop(Process_t *process) {
    kill(process->pid, SIGTRAP);
    WAIT_FOR_SIGNAL(process, SIGSTOP | SIGTRAP);
}

void Process_continue(Process_t *process) {
    const int signum = 0; // leaving this here in case I need to continue with a signal later
    if (!ISRUNNING(process)) {
        ptrace(PTRACE_CONT, process->pid, 0, signum);
        process->flags |= RUNNING;
    }
    
}

long Process_get_word(Process_t *process, void *address) {
    long result = ptrace(PTRACE_PEEKTEXT, process->pid, address, 0);
    if (result == -1) {
        printf("%s:%d %s(): ptrace error %d: %s\n", __FILE__, __LINE__, __func__, errno, strerror(errno));
    }
    return result;
}

void Process_set_word(Process_t *process, void *address, long data) {
    int was_running = ISRUNNING(process);
    if (was_running) {
        Process_stop(process);
    }
    int result = ptrace(PTRACE_POKETEXT, process->pid, address, data);
    if (result == -1) {
        printf("%s:%d %s(): ptrace error %d: %s\n", __FILE__, __LINE__, __func__, errno, strerror(errno));
    }
    if (was_running) {
        Process_continue(process);
    }
}

void Process_free(Process_t **process) {
    Process_t *p = *process;
    if (ISATTACHED(p)) {
        Process_detach(p);
    }
    fclose(p->mem);
    free(p);
    *process = NULL;
}

uint8_t *Process_get_bytes(Process_t *process, void *address, size_t size) {
    #ifdef RUN_READ_BENCHMARK
        benchmarkMemFileVSPtrace(process, address, size);
    #endif
    #ifdef READ_WITH_PTRACE
        // this is about 300 times slower
        return readWithPtrace(process, address, size);
    #else
        return readMemFile(process, address, size);
    #endif
}