from .memory import MemoryMap
from .match import MemoryMatch, Matches


import struct
import time
import math
from .pretty_print import Logger, human_readable, MEMORY_UNITS



class Process:
    def __init__(self, pid):
        self.pid = pid
        self.map = MemoryMap(pid)
        self.log = Logger()
        self.__last_scan_fmt__ = None
        
    
    def __value_to_fmt__(self, value):
        if isinstance(value, float):
            # TODO: Not sure how to differentiate between double and float
            return 'f'
        elif isinstance(value, int):
            is_negative = False
            if value < 0:
                is_negative = True
            if math.abs(value) < 0x100:
                if not is_negative:
                    return '@B'
                if is_negative and math.abs(value) < 0x80:
                    return '@b'
            elif math.abs(value) < 0x10000:
                if not is_negative:
                    return '@H'
                if is_negative and math.abs(value) < 0x8000:
                    return 'h'
            elif math.abs(value) < 0x1000000000000:
                if not is_negative:
                    return '@I'
                if is_negative and math.abs(value) < 0x80000000:
                    return '@i'
            else:
                return '@L' if is_negative else '@l'

    def get_matches(self):
        result = Matches()
        for segment in self.map.segments:
            if len(segment.matches) > 0:
                for offset in segment.matches:
                    match = MemoryMatch(segment, offset)
                    match.fmt = self.__last_scan_fmt__
                    result.append(match)
        return result

    def reset(self):
        for segment in self.map.segments:
            segment.matches = None
    
    @property
    def size(self):
        self.map.update()
        return sum([len(s) for s in self.map.segments])
    
    @property
    def size_pp(self):
        return human_readable(self.size, MEMORY_UNITS)

    def scan(self, value, scan_both=True, memory_segments=None, alignment=4, precision=1):
        """
        Scan this process for the value.

        Parameters:
            value (int or float): The value to be searched, required.
            scan_both (bool): Search for both floats and integers when value is an integer.
                Doesn't matter when value is a float.
            memory_segments (list of MemorySegment): only scan these segments
            alignment (int) - Only search data aligned to this. Higher values increase 
                search speed because we skip non-aligned offsets, but we can miss values
                if the process is not using aligned data, which is rare these days.
            precision (int or float): If searching for a float, consider a match anything between
                value-precision and value+precision.

        Returns:
            Count of matches found

        """
        
        if memory_segments is None:
            self.map.update()
            memorySegments = self.map.segments
        
        

        fmt = self.__value_to_fmt__(value)
        search_value = struct.pack(fmt, value)
        self.__last_scan_fmt__ = fmt
        is_float = 0
        if 'f' in fmt or 'd' in fmt:
            # if format is for a float
            if isinstance(value, int): # but we got an int
                is_float = 2 # search both floats and ints
            else:
                is_float = 1 # only search floats
        
        match_count = 0
        bytes_scanned = 0
        start_time = time.perf_counter()
        
        for i, segment in enumerate(memorySegments):
            speed = bytes_scanned / (time.perf_counter() - start_time)
            # \r\033[K - return carriage and clear the line
            if i > 0:
                self.log.interact(f"\033[K{i+1}/{len(memorySegments)}: Searching {segment} ... {human_readable(speed, MEMORY_UNITS)}/s", end='\r', flush=True)
            bytes_scanned += segment.scan(search_value, alignment, is_float, precision)
            match_count += len(segment.matches)

        self.log.interact(f"\033[K[OK]")
        
        self.__last_scan_value__ = value
        return match_count

