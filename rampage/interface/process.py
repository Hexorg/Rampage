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
        print(f"Process has {humansize(self.map.size(), system=self.shs)} of scannable memory")
        debugger = ptrace.debugger.PtraceDebugger()
        self.__ptrace__ = debugger.addProcess(self.__pid__, False)
        self.map.add_debugger(self.__ptrace__)
        self.__ptrace__.cont()
    
    def get_matches(self):
        result = Matches()
        for segment in self.map.segments:
            if hasattr(segment, '__matches__') and len(segment.__matches__) > 0:
                for offset, types in segment.__matches__.items():
                    result.append(MemoryMatch(segment, offset, types, self.__last_scan_value__))
        return result

    def reset(self):
        for segment in self.map.segments:
            if hasattr(segment, '__matches__'):
                delattr(segment, '__matches__')

    
    def scan(self, value, memorySegments=None, search_types=['@c', '@B', '@h', '@H', '@i', '@I', '@l', '@L', 'f', 'd'], alignment=4):
        """Scan memory segemets for value of the search_type specified.
        Search only for values aligned to alignment byte boundary.

        Keyword arguments:
        value -- the value to be searched, can be anything as long as it can be expressed 
                    as one of the search_types
        memorySegments -- list of MemorySegment objects to search, or None to use all
                    writable memory. Segments must actually be mapped by this process.
                    Useful if you know that your value is likely in a certain segment
                    (e.g. heap). Use `Process.map.find(addressOrPath)` or manually sift
                    through `Process.map.segments` to build this list.
        search_types -- list of raw types to search. Any value usable by struct can be used. 
                    See https://docs.python.org/3.6/library/struct.html
        alignment -- only search byte aligned values. Increases search speed by this factor, but 
                    has a chance to miss values in some programs

        """
        if memorySegments is None:
            memorySegments = self.map.segments
        
        values = {}
        for fmt in search_types:
            try:
                values[fmt] = struct.pack(fmt, value)
            except struct.error:
                continue

        match_count = 0
        bytes_scanned = 0
        has_printed = False
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
                    has_printed = True
                segment.__matches__ = cscan.scan(data, values, alignment)
                bytes_scanned += len(segment)
            match_count += len(segment.__matches__)
        
        if has_printed:
            print()
        
        self.__last_scan_value__ = value
        return match_count

    


    
    @property
    def map(self):
        return self.__memory_map__