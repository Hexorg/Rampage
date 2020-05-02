#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char* argv[], char* envp[]) {
	unsigned int variable = 12;
	pid_t pid = getpid();
	printf("PID: %u", pid);
	printf(" variable address is 0x%lx\n", (unsigned long) &variable);
	printf(">> Press any key to change value\n");
	int is_first_time = 1;
	while (variable != 0xDEADBEEF) {
		if (!is_first_time) {
			variable = random();
		} else {
			is_first_time = 0;
		}
		printf(" Value is %u\n", variable);
		getchar();
	}
	return 0;
}
