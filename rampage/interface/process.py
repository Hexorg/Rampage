from .memory import MemoryMap
from .match import MemoryMatch, Matches
import cscan
import struct
import ctypes
import sys
import time

class cProcess(ctypes.Structure):
    _fields_ = [("pid", ctypes.c_uint),
                 ("flags", ctypes.c_uint),
                 ("mem", ctypes.c_void_p)]

class cMatchOffsets(ctypes.Structure):
    _fields_ = [("matchbuffer", ctypes.POINTER(ctypes.c_size_t)),
                ("size", ctypes.c_size_t)]

class cMatchConditions(ctypes.Structure):
    _fields_ = [("data", ctypes.c_char_p),
                 ("data_length", ctypes.c_int),
                 ("alignment", ctypes.c_int),
                 ("is_float", ctypes.c_int),
                 ("floor", ctypes.c_int)]

def human_readable(value, offsets, format_string="{:.3f}{}"):
    for f, name in offsets:
        if value > f:
            return format_string.format(value / f, name)


def prep_cscan_types(cscan):
    cscan.Process_new.argtypes = [ctypes.c_int]
    cscan.Process_new.restype = ctypes.POINTER(cProcess)
    cscan.Process_continue.argtypes = [ctypes.POINTER(cProcess)]
    cscan.Process_continue.restype = None

    cscan.Process_get_bytes.argtypes = [ctypes.POINTER(cProcess), ctypes.c_void_p, ctypes.c_size_t]
    cscan.Process_get_bytes.restype = ctypes.c_void_p

    cscan.Process_set_word.argtypes = [ctypes.POINTER(cProcess), ctypes.c_void_p, ctypes.c_long]
    cscan.Process_set_word.restype = None

    cscan.scan.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(cMatchConditions)]
    cscan.scan.restype = ctypes.POINTER(cMatchOffsets)
    cscan.filter.argtypes = [ctypes.c_void_p, ctypes.POINTER(cMatchConditions), ctypes.POINTER(cMatchOffsets)]
    cscan.filter.restype = ctypes.POINTER(cMatchOffsets)

class Process(ctypes.Structure):
    size_units = [(1000000000000000, 'PB'), (1000000000000, 'TB'), (1000000000, 'GB'), (1000000, 'MB'), (1000, 'KB'), (1, 'B')]

    def __init__(self, pid):
        cscan = ctypes.cdll.LoadLibrary("cscan/libcscan.so")
        prep_cscan_types(cscan)

        p = cscan.Process_new(pid)
        cscan.Process_continue(p)

        self.__memory_map__ = MemoryMap.Load(cscan, p)
        self.__last_scan_value__ = None
        self.__cscan__ = cscan
        print(f"Process has {human_readable(self.map.size(), Process.size_units)} of scannable memory")
        

    def get_matches(self):
        result = Matches()
        for segment in self.map.segments:
            if hasattr(segment, '__matches__'):
                for i in range(segment.__matches__.contents.size):
                    result.append(MemoryMatch(segment, segment.__matches__.contents.matchbuffer[i], self.__last_scan_value__))
        return result

    def reset(self):
        for segment in self.map.segments:
            if hasattr(segment, '__matches__'):
                delattr(segment, '__matches__')

    
    def scan(self, value, fmt='@i', memorySegments=None, alignment=1):
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

        search_value = struct.pack(fmt, value)

        matchConditions = cMatchConditions(search_value, len(search_value), alignment, 0, 0)

        match_count = 0
        bytes_scanned = 0
        has_printed = False
        start_time = time.clock()
        for i, segment in enumerate(memorySegments):
            data = segment.readBytes()
            if hasattr(segment, '__matches__'):
                # this is a filter run
                if segment.__matches__.contents.size > 0:
                    segment.__matches__ = self.__cscan__.filter(data, ctypes.byref(matchConditions), segment.__matches__)
            else:
                # this is the first time we run, display scan info
                speed = bytes_scanned / (time.clock() - start_time)
                if len(memorySegments) != 1: # if there's only one segment we don't have speed info anyway
                    # \r\033[K - return carriage and clear the line
                    print(f"\r\033[K{i+1}/{len(memorySegments)}: Searching {segment} ... {match_count} matches {human_readable(speed, Process.size_units)}/s", end='')
                    sys.stdout.flush()
                    has_printed = True
                segment.__matches__ = self.__cscan__.scan(data, len(segment), ctypes.byref(matchConditions))
                bytes_scanned += len(segment)
            match_count += segment.__matches__.contents.size
        
        if has_printed:
            print()
        
        self.__last_scan_value__ = value
        return match_count

    


    
    @property
    def map(self):
        return self.__memory_map__