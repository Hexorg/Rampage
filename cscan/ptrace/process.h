#ifndef __CSCAN_PROCESS_H__
#define __CSCAN_PROCESS_H__

#include <sys/types.h>
#include <stdio.h>

typedef struct Process_s {
    pid_t pid;
    unsigned int flags;
    FILE *mem;
} Process_t;

typedef enum ProcessFlags_s {
    ATTACHED = 1,
    RUNNING = 2,
    EXITED = 4
} ProcessFlag_t;

#define ISATTACHED(process) (process->flags & ATTACHED)
#define SETATTACHED(process) (process->flags |= ATTACHED)

#define ISRUNNING(process) (process->flags & RUNNING)
#define SETRUNNING(process) (process->flags |= RUNNING)
#define SETSTOPPED(process) (process->flags &= ~RUNNING)

Process_t* Process_new(int pid);
void Process_attach(Process_t *process);
void Process_detach(Process_t *process);
int Process_wait(Process_t *process, int is_blocking);
void Process_stop(Process_t *process);
void Process_continue(Process_t *process);
long Process_get_word(Process_t *process, void *address);
void Process_set_word(Process_t *process, void *address, long data);
char *Process_get_bytes(Process_t *process, void *address, size_t size);
void Process_free(Process_t **process);
#endif