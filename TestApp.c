#include <stdio.h>

int square(int value) {
	return value*value;
}

int main(int argc, char* argv[], char* envp[]) {
	printf("argc = %d\nargv[0] = %s\nenvp[0] = %s\n", argc, argv[0], envp[0]);
	int variable = 12;
	int another = square(variable);
	int input;
	printf("%d squared is %d\n", variable, another);
	printf("variable address is 0x%llx\n", (unsigned long) &variable);
	printf("Please, enter an integer, writting to 0x%llx\n", (unsigned long) &input);
	scanf("%d",&input);
	printf("%d squared is %d\n", input, square(input)); 
	return 0;
}
