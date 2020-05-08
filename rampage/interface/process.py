from .memory import MemoryMap
from .match import MemoryMatch, Matches
import cscan
import struct
import ptrace.debugger
import sys
import time
from hurry.filesize import size as humansize

class Process:
    shs = [(1000000000000000, 'PB'), (1000000000000, 'TB'), (1000000000, 'GB'), (1000000, 'MB'), (1000, 'KB'), (1, 'B')]
    def __init__(self, pid):
        self.__pid__ = int(pid)
        self.__last_scan_value__ = None
    
    def attach(self):
        self.__memory_map__ = MemoryMap.fromFile(f"/proc/{self.__pid__}/maps")
        print(f"Process has {humansize(self.__memory_map__.size(), system=self.shs)} of scannable memory")
        debugger = ptrace.debugger.PtraceDebugger()
        self.__ptrace__ = debugger.addProcess(self.__pid__, False)
        self.__memory_map__.add_debugger(self.__ptrace__)
        self.__ptrace__.cont()
    
    def get_matches(self):
        print("get_matches()")
        result = Matches()
        print("entering loop")
        for segment in self.__memory_map__.segments:
            print("in a loop")
            if hasattr(segment, '__matches__') and len(segment.__matches__) > 0:
                print(f"Segment {segment} has matches")
                for offset, types in segment.__matches__.items():
                    print(f"adding offset {hex(offset)}")
                    result.append(MemoryMatch(segment, offset, types, self.__last_scan_value__))
        return result

    def reset(self):
        for segment in memorySegments:
            if hasattr(segment, '__matches__'):
                delattr(segment, '__matches__')

    
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
        bytes_scanned = 0
        start_time = time.clock()
        for i, segment in enumerate(memorySegments):

            try:
                data = self.__ptrace__.readBytes(segment.start, len(segment))
            except Exception as e:
                print(f"Error while reading bytes from {segment}: {segment.path}")
                print(e)
                continue
            if hasattr(segment, '__matches__'):
                # this is a filter run
                if len(segment.__matches__) > 0:
                    segment.__matches__ = cscan.filter(data, values, segment.__matches__)
            else:
                # this is the first time we run, display scan info
                speed = bytes_scanned / (time.clock() - start_time)
                if len(memorySegments) != 1: # if there's only one segment we don't have speed info anyway
                    # \r\033[K - return carriage and clear the line
                    print(f"\r\033[K{i+1}/{len(memorySegments)}: Searching {segment} ... {match_count} matches {humansize(speed, system=self.shs)}/s", end='')
                    sys.stdout.flush()
                segment.__matches__ = cscan.scan(data, values)
                bytes_scanned += len(segment)
            match_count += len(segment.__matches__)
            
        print()
        
        self.__last_scan_value__ = value
        return match_count

    


    
    @property
    def maps(self):
        return self.__memory_map__