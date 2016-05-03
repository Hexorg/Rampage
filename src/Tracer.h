#ifndef __TRACER_H__
#define __TRACER_H__

#include <exception>

namespace System {

#define NULL 0

class TracerException: public std::exception {
public:
	TracerException(const char *error);
	const char* what() const throw();
private:
	const char *error;
};

class Tracer {
public:
	Tracer(unsigned int pid, bool pauseOnStart = false);
	~Tracer();

	unsigned long getMemory(unsigned long address);
private:
	unsigned int pid;
};


}
#endif
