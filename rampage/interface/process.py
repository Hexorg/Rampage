from .memory import MemoryMap
from .types import StructMatch

import ptrace.debugger
class Process:
    def __init__(self, pid):
        self.__pid__ = int(pid)
    
    def attach(self):
        self.__memory_map__ = MemoryMap.fromFile(f"/proc/{self.__pid__}/maps")
        debugger = ptrace.debugger.PtraceDebugger()
        self.__ptrace__ = ptrace.debugger.PtraceProcess(debugger, self.__pid__, False)
        self.__ptrace__.cont()
    
    def scan(self, value, memorySegments=None):
        if memorySegments is None:
            memorySegments = self.__memory_map__.segments
        
        matches = set()

        for segment in memorySegments:
            try:
                data = self.__ptrace__.readBytes(segment.start, len(segment))
            except Exception as e:
                print(f"Error while reading bytes from {segment}: {segment.path}")
                print(e)
                continue

            for offset in range(0, len(data), 4):
                # if offset % int(len(data)/256) == 0:
                #     print(100*(offset/len(data)), f"% ... {len(matches)} matches")
                match = StructMatch.match(value, data, offset)
                if match:
                    match.segment = segment
                    matches.add(match)
        
        return matches
    
    def filter(self, value, matches):
        new_matches = set()
        for match in matches:
            data = self.__ptrace__.readBytes(match.address, 4)
            new_match = StructMatch.match(value, data, 0)
            if new_match:
                new_match.offset = match.offset
                new_match.segment = match.segment
                new_matches.add(new_match)
        return new_matches



    
    @property
    def maps(self):
        return self.__memory_map__