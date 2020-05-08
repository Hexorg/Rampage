from .memory import MemoryMap
from .match import MemoryMatch, Matches
import cscan
import struct
import ptrace.debugger

class Process:
    def __init__(self, pid):
        self.__pid__ = int(pid)
        self.__last_scan_value__ = None
    
    def attach(self):
        self.__memory_map__ = MemoryMap.fromFile(f"/proc/{self.__pid__}/maps")
        debugger = ptrace.debugger.PtraceDebugger()
        self.__ptrace__ = debugger.addProcess(self.__pid__, False)
        self.__memory_map__.add_debugger(self.__ptrace__)
        self.__ptrace__.cont()
    
    def get_matches(self):
        result = Matches()
        for segment in self.__memory_map__.segments:
            if hasattr(segment, '__matches__') and len(segment.__matches__) > 0:
                for offset, types in segment.__matches__.items():
                    result.append(MemoryMatch(segment, offset, types, self.__last_scan_value__))
        return result                

    
    def scan(self, value, memorySegments=None, search_types=['@c', '@B', '@h', '@H', '@i', '@I', '@l', '@L', 'f', 'd']):
        if memorySegments is None:
            memorySegments = self.__memory_map__.segments
        
        values = {}
        for fmt in search_types:
            try:
                values[fmt] = struct.pack(fmt, value)
            except struct.error:
                continue

        match_count = 0
        for segment in memorySegments:
            if segment.path == '[vvar]' or segment.path == '[vsyscall]':
                continue
            try:
                data = self.__ptrace__.readBytes(segment.start, len(segment))
            except Exception as e:
                print(f"Error while reading bytes from {segment}: {segment.path}")
                print(e)
                continue
            if hasattr(segment, '__matches__'):
                if len(segment.__matches__) > 0:
                    segment.__matches__ = cscan.filter(data, values, segment.__matches__)
            else:
                segment.__matches__ = cscan.scan(data, values)
            match_count += len(segment.__matches__)
        
        self.__last_scan_value__ = value
        return match_count

    


    
    @property
    def maps(self):
        return self.__memory_map__