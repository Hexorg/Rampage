from enum import Enum
import bisect
import re
import os
from signal import SIGTRAP, SIGSTOP

from .crampage import CScan, cMatchConditions_s, cMatchOffsets_s
from ctypes import POINTER

from .pretty_print import Logger
class Permission(Enum):
    PRIVATE = 'p'
    EXECUTE = 'x'
    WRITE = 'w'
    READ = 'r'
    SHARED = 's'

class MemorySegment:
    '''
    A single, continious memory segment
    '''
    def __init__(self, cscan):
        self.start = 0
        self.end = 0
        self.permissions = set()
        self.offset = 0
        self.dev_major = 0
        self.dev_minor = 0
        self.inode = 0
        self.path = ''
        self.log = Logger()
        self.__matches__ = None
        self.cscan = cscan
    
    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.end <= other.start
        elif isinstance(other, int):
            return self.end < other
    
    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.start >= other.end
        elif isinstance(other, int):
            return self.start > other
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return hash(self) == hash(other)
        elif isinstance(other, int):
            return other in self
    
    def __hash__(self):
        h = hash(self.start) ^ hash(len(self))
        if len(self.path) != 0:
            h ^= hash(self.path)
        return h
    
    def __len__(self):
        return self.end - self.start
    
    def __contains__(self, other):
        if isinstance(other, int):
            return self.start < other < self.end
    
    def __repr__(self):
        if self.path:
            short_path = self.path
            if len(self.path) > 40:
                path_split = os.path.split(short_path)
                short_path = path_split[1]
                while len(short_path) < 30:
                    path_split = os.path.split(path_split[0])
                    if len(os.path.join(path_split[1], short_path)) > 30:
                        break
                    short_path = os.path.join(path_split[1], short_path)
                short_path = self.path[:40-len(short_path)] + '...' + short_path
            return f"<{self.__class__.__name__}{self.__id__} {short_path}>"
        else:
            return f"<{self.__class__.__name__}{self.__id__} {hex(self.start)}-{hex(self.end)}>"
    
    @property
    def info(self):
        return f"Segment:\n  {hex(self.start)}-{hex(self.end)}\n  {self.permissions}\n  Offset: {hex(self.offset)}\n  Device {self.dev_major}:{self.dev_minor}\n  Inode: {self.inode}\n  {self.path}"
    
    @property
    def matches(self):
        '''Returns cMatchConditions_s'''
        if self.__matches__ is None:
            return None
        return self.__matches__.contents
    
    @matches.setter
    def matches(self, value):
        '''Accepts POINTER to cMatchConditions_s'''
        if self.__matches__ is not None:
            self.cscan.free_matched_offsets(self.__matches__)
        self.__matches__ = value
                    
    
    def scan(self, data, alignment, is_float, precision):
        if self.__matches__ is not None:
            if len(self.matches) > 0:
                self.matches = self.cscan.run_filter(self.start, len(self), data, self.__matches__, alignment, is_float, precision)
            return len(self.matches) * len(data)
        else:
            self.matches = self.cscan.run_scan(self.start, len(self), data, alignment, is_float, precision)
            return len(self)

        
    
    def read_bytes(self, offset=0, size=0):
        if size == 0:
            size = len(self)
        return self.cscan.read_bytes(self.start+offset, size)
    
    def write_bytes(self, offset, data):
        self.cscan.write_bytes(self.start+offset, data)
                


class MemoryMap:
    '''
    Each process in Linux does not have raw access to RAM, but uses memory mapping 
    provided by Linux kernel. The kernel creates /proc/<pid>/maps file for each process and 
    this class checks what addresses are allocated by that process.
    '''
    def __procmaps_path__(self):
        return f"/proc/{self.pid}/maps"
    
    def __parse_line__(self, line):
        data = line.split()
        item1, item2 = data[0].split('-')

        entry = MemorySegment(self.cscan)
        entry.start = int(item1, 16)
        entry.end = int(item2, 16)
        for character in data[1]:
            if character != '-':
                entry.permissions.add(Permission(character))
        entry.offset = int(data[2], 16)
        item1, item2 = data[3].split(':')
        entry.dev_major = int(item1, 10)
        entry.dev_minor = int(item2, 10)
        entry.inode = int(data[4], 10)
        entry.path = (' '.join(data[5:])).strip()

        return entry

    def __init__(self, pid):
        self.__segments__ = []
        self.__ignore_paths__ = re.compile(r'/dev/.*|/memfd.*|\[vvar\]|\[vsyscall\]')
        self.__ignore_without_permissions__ = set([Permission.WRITE])
        self.pid = pid
        self.cscan = CScan(pid)

    def __len__(self):
        return len(self.__segments__)
    
    def update(self):
        '''
        Re-parse the file
        '''
        with open(self.__procmaps_path__(), 'r') as f:
            for line in f:
                entry = self.__parse_line__(line)
                if len(self.__segments__) == 0:
                    entry.__id__ = 0
                    self.__segments__.append(entry)
                else:
                    index = bisect.bisect_left(self.__segments__, entry)
                    if index == len(self.__segments__):
                        entry.__id__ = len(self.__segments__)
                        self.__segments__.append(entry)
                    else:
                        this_segment = self.__segments__[index]
                        if this_segment == entry:
                            pass
                        elif this_segment.start == entry.start or (index > 0 and index+1 < len(self.__segments__) and self.__segments__[index-1] < entry < self.__segments__[index+1]):
                            entry.__id__ = this_segment.__id__
                            entry.matches = this_segment.__matches__
                            self.__segments__[index] = entry
                        elif index+1 < len(self.__segments__) and this_segment.start == entry.start and self.__segments__[index+1].end == entry.end:
                            entry.__id__ = this_segment.__id__
                            entry.matches = this_segment.__matches__
                            self.__segments__[index] = entry
                            removed_segment = self.__segments__.pop(index+1)
                            if removed_segment.matches is not None:
                                print("WARNING: Two segments merged and have matches. Currently unsupported. Dropping matches of second segment")
                        elif entry < this_segment:
                            entry.__id__ = len(self.__segments__)
                            self.__segments__.insert(index, entry)
                        else:
                            print(this_segment == entry, this_segment < entry, this_segment > entry)
                            print(len(self), index, sep=', ', end=' - ')
                            print(self.__segments__[index-1].info, this_segment.info, self.__segments__[index+1].info, entry.info, sep=';\n')

                
    
    def size(self):
        '''
        Returns:
            Size of scannable memory
        '''
        return sum([len(s) for s in self.segments])
    
    def find(self, addressOrPath):
        '''
        Find the segment of memory that maps a given address, or the first segment that 
        maps a given path

        Parameters:
            addressOrPath (int or string) - address allocated by the process, or a path to
                file mapped by the process.
        '''
        self.update()
        if isinstance(addressOrPath, str):
            for segment in self.segments:
                if addressOrPath == segment.path:
                    return segment    
        else:
            index = bisect.bisect_left(self.__segments__, addressOrPath)
            entry = self.__segments__[index]
            if addressOrPath in entry:
                return entry
        return None
    
    @property
    def segments(self):
        '''
        Returns segments that are writable and not device files
        '''
        result = []
        for segment in self.__segments__:
            if self.__ignore_paths__.match(segment.path):
                continue
            # if segment.dev_major == 0 and segment.dev_minor == 0:
            #     continue
            is_ignore = False
            for ignored_permission in self.__ignore_without_permissions__:
                if ignored_permission not in segment.permissions:
                    is_ignore = True
                    break
            if is_ignore:
                continue
            segment.__id__ = len(result)
            result.append(segment)
        return result
    

