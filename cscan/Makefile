src = $(shell find src/ -type f -name '*.c')
obj = $(src:.c=.o)

LDFLAGS = -lm
CFLAGS = -O2

.PHONY: all
all: libcscan.so test

libcscan.so: $(obj)
	$(CC) -shared -o $@ $^ $(LDFLAGS)

test: libcscan.so src/standalone.o
	$(CC) $(CFLAGS) -L . -lcscan -o test src/standalone.o 

%.o: %.c
	$(CC) -Wall -Werror -fpic $(CFLAGS) -o $@ -c $<


.PHONY: clean
clean:
	rm -f $(obj) libcscan.so test