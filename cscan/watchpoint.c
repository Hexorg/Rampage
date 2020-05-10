/*
 * From 
 * https://stackoverflow.com/questions/8941711/is-it-possible-to-set-a-gdb-watchpoint-programmatically
 */
#include <signal.h>
#include <syscall.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>
#include <sys/ptrace.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <linux/user.h>

enum {
    DR7_BREAK_ON_EXEC  = 0,
    DR7_BREAK_ON_WRITE = 1,
    DR7_BREAK_ON_RW    = 3,
};

enum {
    DR7_LEN_1 = 0,
    DR7_LEN_2 = 1,
    DR7_LEN_4 = 3,
};

typedef struct {
    char l0:1;
    char g0:1;
    char l1:1;
    char g1:1;
    char l2:1;
    char g2:1;
    char l3:1;
    char g3:1;
    char le:1;
    char ge:1;
    char pad1:3;
    char gd:1;
    char pad2:2;
    char rw0:2;
    char len0:2;
    char rw1:2;
    char len1:2;
    char rw2:2;
    char len2:2;
    char rw3:2;
    char len3:2;
} dr7_t;

typedef void sighandler_t(int, siginfo_t*, void*);

int watchpoint(void* addr, sighandler_t handler)
{
    pid_t child;
    pid_t parent = getpid();
    struct sigaction trap_action;
    int child_stat = 0;

    sigaction(SIGTRAP, NULL, &trap_action);
    trap_action.sa_sigaction = handler;
    trap_action.sa_flags = SA_SIGINFO | SA_RESTART | SA_NODEFER;
    sigaction(SIGTRAP, &trap_action, NULL);

    if ((child = fork()) == 0)
    {
        int retval = EXIT_SUCCESS;

        dr7_t dr7 = {0};
        dr7.l0 = 1;
        dr7.rw0 = DR7_BREAK_ON_WRITE;
        dr7.len0 = DR7_LEN_4;

        if (ptrace(PTRACE_ATTACH, parent, NULL, NULL))
        {
            exit(EXIT_FAILURE);
        }

        sleep(1);

        if (ptrace(PTRACE_POKEUSER, parent, offsetof(struct user, u_debugreg[0]), addr))
        {
            retval = EXIT_FAILURE;
        }

        if (ptrace(PTRACE_POKEUSER, parent, offsetof(struct user, u_debugreg[7]), dr7))
        {
            retval = EXIT_FAILURE;
        }

        if (ptrace(PTRACE_DETACH, parent, NULL, NULL))
        {
            retval = EXIT_FAILURE;
        }

        exit(retval);
    }

    waitpid(child, &child_stat, 0);
    if (WEXITSTATUS(child_stat))
    {
        printf("child exit !0\n");
        return 1;
    }

    return 0;
}

int var;

void trap(int sig, siginfo_t* info, void* context)
{
    printf("new value: %d\n", var);
}

int main(int argc, char * argv[])
{
    int i;

    printf("init value: %d\n", var);

    watchpoint(&var, trap);

    for (i = 0; i < 100; i++) {
        var++;
        sleep(1);
    }

    return 0;
}