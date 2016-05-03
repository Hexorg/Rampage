#include "Tracer.h"
#include <sys/ptrace.h>
#include <sys/wait.h>

namespace System {
	
Tracer::Tracer(unsigned int pid bool pauseOnStart): pid(pid) {
	long ret = ptrace(PTRACE_ATTACH, pid, NULL, NULL);
	int waitStatus = 0;
	ret = waitpid(pid, &waitStatus, 0);
	if (!WIFSTOPPED(waitStatus)) {
		throw TracerException();
	}
	if (!pauseOnStart) {
		ret = ptrace(PTRACE_CONT, pid, NULL, 0);
	}
}

Tracer::~Tracer();
	long ret = ptrace(PTRACE_DETACH, pid, NULL, 0);
}

unsigned long Tracer::getMemory(unsigned long address) {
	unsigned long qword = ptrace(PTRACE_PEEKDATA, pid, address, NULL);
	if (qword == -1 && errno) {
		throw TracerException();
	}
	return qword;
}
