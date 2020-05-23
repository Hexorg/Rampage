
import struct 
import __main__ as main_import

def filter_printable_bytes(buffer):
    data = bytearray('................', 'utf-8')
    assert(len(buffer) == len(data))
    for i, b in enumerate(buffer):
        if b > 0x1F and b < 0x7F:
            data[i] = b
    return data.decode('utf-8')

MEMORY_UNITS = [(1000000000000000, 'PB'), (1000000000000, 'TB'), (1000000000, 'GB'), (1000000, 'MB'), (1000, 'KB'), (1, 'B')]

def human_readable(value, units=MEMORY_UNITS, format_string="{:.3f}{}"):
    for f, name in units:
        if value > f:
            return format_string.format(value / f, name)

def hexdump(buffer, offset_start, fmt='@B'):
    bytes_in_line = 16

    print_format = '{}'
    width = 0
    if 'B' in fmt:
        print_format = '{0:2x}'
        width = 2
    elif 'b' in fmt:
        print_format = '{0:3}'
        width = 3
    elif 'H' in fmt or 'h' in fmt:
        print_format = '{0:6}'
        width = 6
    elif 'I' in fmt or 'i' in fmt:
        print_format = '{0:11}'
        width = 11
    elif 'f' in fmt or 'd' in fmt:
        print_format = '{0:11.2f}'
        width = 11

    struct_size = struct.calcsize(fmt)
    print('{0:>16}'.format("offset"), end=' ')
    for column_offset in range(0, bytes_in_line, struct_size):
        if column_offset == bytes_in_line//2:
                print(' ', end='')
        offset_format = '{0:>'+str(width)+'}'
        print(offset_format.format('-{:01x}'.format((offset_start + column_offset) & 0xF)), end=' ')
    print()

    for line_offset in range(0, len(buffer), bytes_in_line):
        line_address = offset_start + line_offset
        print('{:016x}'.format(line_address), end=' ')
        for value_offset in range(0, bytes_in_line, struct_size):
            if value_offset == bytes_in_line//2:
                print(' ', end='')
            value = struct.unpack_from(fmt, buffer, line_offset+value_offset)[0]
            if 'f' in fmt or 'd' in fmt:
                if value > 1000.0 or value < 0.01:
                    if value == 0.0:
                        print_format = '{0:>11}'.format(0)
                    else:
                        print_format = '{0:11.2e}'
                else:
                    print_format = '{0:11.2f}'
            print(print_format.format(value), end=' ')

        print(f' |{filter_printable_bytes(buffer[line_offset:line_offset+bytes_in_line])}|') 

class Logger:
    def __init__(self):
        self.is_interactive = not hasattr(main_import, '__file__')

    def interact(self, *args, sep=' ', end='\n', flush=False):
        if self.is_interactive:
            print(*args, sep=sep, end=end, flush=flush)
