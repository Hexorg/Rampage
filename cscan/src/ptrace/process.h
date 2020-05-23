#ifndef __CSCAN_PROCESS_H__
#define __CSCAN_PROCESS_H__

#include <sys/types.h>
#include <stdio.h>
#include <inttypes.h>

typedef struct Process_s {
    pid_t pid;
    unsigned int flags;
    pid_t attached_pid;
    pid_t attached_tid;
    FILE *mem;
} Process_t;

typedef enum ProcessFlags_s {
    ATTACHED = 1,
    RUNNING = 2,
    EXITED = 4
} ProcessFlag_t;

#ifdef SYS_gettid
#define ISATTACHED(process) (process->flags & ATTACHED)
#define SETATTACHED(process) do { process->flags |= ATTACHED; process->attached_pid = getpid(); process->attached_tid = syscall(SYS_gettid); } while(0)
#define SETDETTACHED(process) process->flags &= ~ATTACHED
#define ISATTACHEDPID(process) (process->attached_pid == getpid() && process->attached_tid == syscall(SYS_gettid))
#else
#error "This library requires use of SYS_gettid syscall. It's unavailable on this system"
#endif

#define ISRUNNING(process) (process->flags & RUNNING)
#define SETRUNNING(process) (process->flags |= RUNNING)
#define SETSTOPPED(process) (process->flags &= ~RUNNING)

extern Process_t* Process_new(int pid);
extern void Process_attach(Process_t *process);
extern void Process_detach(Process_t *process);
extern int Process_wait(Process_t *process, int is_blocking);
extern void Process_stop(Process_t *process);
extern void Process_continue(Process_t *process);
extern long Process_get_word(Process_t *process, void *address);
extern void Process_set_word(Process_t *process, void *address, long data);
extern uint8_t *Process_get_bytes(Process_t *process, void *address, size_t size);
extern void Process_free_bytes(uint8_t *bytes);
extern void Process_free(Process_t **process);
#endif