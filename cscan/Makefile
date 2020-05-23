src = $(shell find src/ -type f -name '*.c')
obj = $(src:.c=.o)

LDFLAGS = -lm
CFLAGS = -O2

.PHONY: all
all: librampage.so test

librampage.so: $(obj)
	$(CC) -shared -o $@ $^ $(LDFLAGS)

test: librampage.so src/standalone.o
	$(CC) $(CFLAGS) -L . -lrampage -o test src/standalone.o 

%.o: %.c
	$(CC) -Wall -Werror -fpic $(CFLAGS) -o $@ -c $<


.PHONY: clean
clean:
	rm -f $(obj) librampage.so test
