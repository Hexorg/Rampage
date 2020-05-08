import struct

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
    def __init__(self, segment, offset, typematch, lastValue=None):
        self.__segment__ = segment
        self.__offset__ = offset
        self.__typematch__ = typematch
        self.lastValue = lastValue
    
    def __repr__(self):
        if self.lastValue is None:
            return f"<Match {hex(self.__segment__.start + self.__offset__)} {self.__typematch__} in {self.__segment__}>"
        else:
            return f"<Match {hex(self.__segment__.start + self.__offset__)} - {self.lastValue} in {self.__segment__}>"

    def update(self):
        fmt = list(self.__typematch__)[0]
        length = struct.calcsize(fmt)
        data = self.__segment__.readBytes(self.__offset__, length)
        self.lastValue = struct.unpack(fmt, data)[0]
        return self.lastValue

    def set(self, value, isContinue=True):
        data = None

        for fmt in self.__typematch__:
            try:
                data = struct.pack(fmt, value)
            except struct.error:
                continue
            if data is not None: 
                break
        if data is None:
            raise TypeError(f"Can not convert {value} into any matched field types {self.__typematch__}")

        self.__segment__.writeBytes(self.__offset__, data, isContinue)