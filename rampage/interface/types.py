import ctypes
import struct 

class Match:
    def __init__(self):
        self.types = set()
        self.offset = 0
        self.value = 0
        self.segment = None
    
    @property
    def address(self):
        return self.segment.start + self.offset
    
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.types} {hex(self.address)} {self.segment}>"

class CTypeMatch:
    search_types = [ctypes.c_byte, 
            ctypes.c_float, 
            ctypes.c_double, 
            ctypes.c_int16, 
            ctypes.c_int32, 
            ctypes.c_int64, 
            ctypes.c_uint16,
            ctypes.c_uint32, 
            ctypes.c_uint64]



    
    @classmethod
    def match(cls, value, buffer, offset):
        
        m = Match()
        for T in CTypeMatch.search_types:
            try:
                data = T.from_buffer(buffer, offset)
                if (data.value == value):
                    m.types.add(T)
                    m.value = value
                    m.offset = offset
            except ValueError as e:
                pass
        return m
    
class StructMatch:
    @classmethod
    def match(cls, value, buffer, offset):
        
        if len(buffer) - offset >= 4:
            data = struct.unpack_from("@i", buffer, offset)
            if (data[0] == value):
                m = Match()
                m.types.add("@i")
                m.value = value
                m.offset = offset
                return m