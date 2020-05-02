from enum import Enum
import bisect

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
        if self.path.strip():
            return f"<{self.__class__.__name__} {self.path}>"
        else:
            return f"<{self.__class__.__name__} {hex(self.start)}-{hex(self.end)}>"

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
                entry.path = ' '.join(data[5:])
                m.add(entry)
            return m
            

    def __init__(self):
        self.__segments__ = []
    
    def __len__(self):
        return len(self.__segments__)
    
    def add(self, segment):
        self.__segments__.append(segment)
    
    def get(self, address):
        index = bisect.bisect_left(self.__segments__, address)
        entry = self.__segments__[index]
        if address in entry:
            return entry
        else:
            raise IndexError("Given address is not mapped by this memory map")
    
    @property
    def segments(self):
        return self.__segments__
    

