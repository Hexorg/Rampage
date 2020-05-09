from enum import Enum
import bisect
import re
from signal import SIGTRAP, SIGSTOP
class Permission(Enum):
    PRIVATE = 'p'
    EXECUTE = 'x'
    WRITE = 'w'
    READ = 'r'
    SHARED = 's'

class MemorySegment:
    def __init__(self):
        self.start = 0
        self.end = 0
        self.permissions = set()
        self.offset = 0
        self.dev_major = 0
        self.dev_minor = 0
        self.inode = 0
        self.path = ''
    
    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return self.start < other.start
        elif isinstance(other, int):
            return self.end < other
    
    def __gt__(self, other):
        if isinstance(other, self.__class__):
            return self.start > other.start
        elif isinstance(other, int):
            return self.start > other
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.start == other.start and self.end == other.end and self.path == other.path
        elif isinstance(other, int):
            return other in self
    
    def __len__(self):
        return self.end - self.start
    
    def __contains__(self, other):
        if isinstance(other, int):
            return self.start < other < self.end
    
    def __repr__(self):
        if self.path:
            return f"<{self.__class__.__name__} {self.path}>"
        else:
            return f"<{self.__class__.__name__} {hex(self.start)}-{hex(self.end)}>"
    
    @property
    def info(self):
        return f"Segment:\n  {hex(self.start)}-{hex(self.end)}\n  {self.permissions}\n  Offset: {hex(self.offset)}\n  Device {self.dev_major}:{self.dev_minor}\n  Inode: {self.inode}\n  {self.path}"
    
    def readBytes(self, offset, size):
        return self.__ptrace__.readBytes(self.start + offset, size)
    
    def writeBytes(self, offset, data, isContinue=True):
        if not self.__ptrace__.is_stopped:
            self.__ptrace__.kill(SIGTRAP)
            self.__ptrace__.waitSignals(SIGTRAP)
            self.__ptrace__.is_stopped = True
        result = self.__ptrace__.writeBytes(self.start + offset, data)
        if isContinue:
            self.__ptrace__.cont()
        return result

class MemoryMap:
    @classmethod
    def fromFile(cls, path):
        with open(path, 'r') as f:
            m = MemoryMap()
            for line in f:
                data = line.split()
                item1, item2 = data[0].split('-')

                entry = MemorySegment()
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
                m.add(entry)
            return m
            

    def __init__(self):
        self.__segments__ = []
        self.__ignore_paths__ = re.compile(r'/dev/.*|/memfd.*|\[vvar\]|\[vsyscall\]')
        self.__ignore_without_permissions__ = set([Permission.WRITE])
    
    def __len__(self):
        return len(self.segments)
    
    def add(self, segment):
        self.__segments__.append(segment)
    
    def size(self):
        return sum([len(s) for s in self.segments])
    
    def add_debugger(self, ptrace):
        for segment in self.segments:
            segment.__ptrace__ = ptrace
    
    def find(self, addressOrPath):
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
            result.append(segment)
        return result
    

