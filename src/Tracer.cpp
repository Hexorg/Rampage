#include "Tracer.h"
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <errno.h>

#include <sstream>
#include <string.h>
#include <iostream>

namespace System {
	
Tracer::Tracer(unsigned int pid, bool pauseOnStart): pid(pid) {
	long ret = ptrace(PTRACE_ATTACH, pid, NULL, NULL);
	std::cout << "ret is " << ret << std::endl;
	int waitStatus = 0;
	ret = waitpid(pid, &waitStatus, 0);
	std::cout << "ret is " << ret << std::endl;
	if (!WIFSTOPPED(waitStatus)) {
		throw TracerException("WIFSTOPPED in false");
	}
	if (!pauseOnStart) {
		ret = ptrace(PTRACE_CONT, pid, NULL, 0);
	std::cout << "ret is " << ret << std::endl;
	}
	std::cout << "Done constructor\n";
}

Tracer::~Tracer() {
	long ret = ptrace(PTRACE_DETACH, pid, NULL, 0);
}

unsigned long Tracer::getMemory(unsigned long address) {
	unsigned long qword = ptrace(PTRACE_PEEKDATA, pid, address, NULL);
	if (qword == -1 && errno) {
		std::stringstream ss;
		ss << "Error is set to " << strerror(errno);
		throw TracerException(ss.str().c_str());
	}
	return qword;
}

TracerException::TracerException(const char *error): error(error) {}
const char* TracerException::what() const throw() {
	return error;
}

}
