import struct, ctypes

class Matches(list):
    def set(self, value):
        for match in self:
            match.set(value, False)
        for match in self:
            match.__segment__.__ptrace__.cont()
            break
    
    def update(self):
        for match in self:
            match.update()

class MemoryMatch:
    def __init__(self, segment, offset, lastValue=None):
        self.__segment__ = segment
        self.__offset__ = offset
        self.lastValue = lastValue
    
    def __repr__(self):
        return f"<Match {hex(self.__segment__.start + self.__offset__)} - {self.lastValue} in {self.__segment__}>"
    
    @property
    def segment(self):
        return self.__segment__
    
    @property
    def offset(self):
        return self.__offset__

    def update(self, fmt='@i'):
        length = struct.calcsize(fmt)
        data = self.segment.readBytes(self.offset, length)
        data = ctypes.cast(data, ctypes.POINTER(ctypes.c_byte * length))
        self.lastValue = struct.unpack(fmt, bytes(data.contents))[0]
        return self.lastValue

    def set(self, value, fmt='@i', isContinue=True):
        data = struct.pack(fmt, value)
        whatsThere = self.segment.readBytes(self.offset, 8)
        whatsThere = bytes(ctypes.cast(whatsThere, ctypes.POINTER(ctypes.c_byte * 8)).contents)
        data = struct.unpack('@L', data + whatsThere[len(data):])[0]
        self.segment.writeWord(self.offset, ctypes.c_long(data))