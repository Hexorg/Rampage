#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define VAR_TYPE unsigned int
#define VAR_TYPE_FORMAT " Value is %d"

int main(int argc, char* argv[], char* envp[]) {
	VAR_TYPE variable = 12;
	pid_t pid = getpid();
	printf("PID: %u", pid);
	printf(" variable address is 0x%lx - %ld bytes\n", (unsigned long) &variable, sizeof(VAR_TYPE));
	printf(">> Press any key to change value\n");
	int is_first_time = 1;
	while (variable != 0xdeadbeef) {
		if (!is_first_time) {
			variable = (VAR_TYPE) random();
		} else {
			is_first_time = 0;
		}
		printf(VAR_TYPE_FORMAT, variable);
		fflush(stdout);
		getchar();
	}
	printf("0xdeadbeef detected. Exiting\n");
	return 0;
}
