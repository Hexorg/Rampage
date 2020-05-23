import ctypes
import struct

class cProcess_s(ctypes.Structure):
    _fields_ = [("pid", ctypes.c_uint),
                 ("flags", ctypes.c_uint),
                 ("attached_pid", ctypes.c_uint),
                 ("attached_tid", ctypes.c_uint),
                 ("mem", ctypes.c_void_p)]

class cMatchOffsets_s(ctypes.Structure):
    _fields_ = [("matchbuffer", ctypes.POINTER(ctypes.c_size_t)),
                ("size", ctypes.c_size_t)]
    
    def __init__(self):
        super().__init__()
        self.__iter_pos__ = 0
    
    def __iter__(self):
        self.__iter_pos__ = 0
        return self

    def __next__(self):
        if self.__iter_pos__ == self.size:
            raise StopIteration
        else:
            result = self.matchbuffer[self.__iter_pos__]
            self.__iter_pos__ += 1
            return result

    def __len__(self):
        return self.size

class cMatchConditions_s(ctypes.Structure):
    _fields_ = [("data", ctypes.c_char_p),
                 ("data_length", ctypes.c_int),
                 ("alignment", ctypes.c_int),
                 ("is_float", ctypes.c_int),
                 ("floor", ctypes.c_float)]

class CScan(ctypes.CDLL):
    def __init__(self, pid):
        super().__init__("cscan/librampage.so")
        self.Process_new.argtypes = [ctypes.c_int]
        self.Process_new.restype = ctypes.POINTER(cProcess_s)
        self.Process_free.argtypes = [ctypes.POINTER(cProcess_s)]
        self.Process_free.restype = None

        self.Process_get_bytes.argtypes = [ctypes.POINTER(cProcess_s), ctypes.c_void_p, ctypes.c_size_t]
        self.Process_get_bytes.restype = ctypes.c_void_p

        self.Process_free_bytes.argtypes = [ctypes.c_void_p]
        self.Process_free_bytes.restype = None

        self.Process_set_word.argtypes = [ctypes.POINTER(cProcess_s), ctypes.c_void_p, ctypes.c_long]
        self.Process_set_word.restype = None

        self.scan.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(cMatchConditions_s)]
        self.scan.restype = ctypes.POINTER(cMatchOffsets_s)
        self.filter.argtypes = [ctypes.c_void_p, ctypes.POINTER(cMatchConditions_s), ctypes.POINTER(cMatchOffsets_s)]
        self.filter.restype = ctypes.POINTER(cMatchOffsets_s)
        self.free_matched_offsets.argtypes = [ctypes.POINTER(cMatchOffsets_s)]
        self.free_matched_offsets.restype = None

        self.__process_ptr__ = self.Process_new(pid)
    
    @property
    def pid(self):
        return self.__process_ptr__.contents.pid

    def close(self, pid):
        self.Process_Free(self.__process_ptr__)
    
    def read_bytes(self, address, size):
        data_ptr = self.Process_get_bytes(self.__process_ptr__, address, size)
        result = bytes(ctypes.cast(data_ptr, ctypes.POINTER(ctypes.c_byte * size)).contents)
        self.Process_free_bytes(data_ptr)
        return result
    
    def write_bytes(self, address, data):
        whatsThere = self.read_bytes(address, 8)
        result = struct.unpack('@L', data + whatsThere[len(data):])[0]
        self.Process_set_word(self.__process_ptr__, address, ctypes.c_long(result))

    def run_scan(self, address, size, search_value, alignment, is_float, precision):
        data_ptr = self.Process_get_bytes(self.__process_ptr__, address, size)
        matchConditions = cMatchConditions_s(search_value, len(search_value), alignment, is_float, precision)
        result = self.scan(data_ptr, size, ctypes.byref(matchConditions))
        self.Process_free_bytes(data_ptr)
        return result
    
    def run_filter(self, address, size, search_value, matches, alignment, is_float, precision):
        data_ptr = self.Process_get_bytes(self.__process_ptr__, address, size)
        matchConditions = cMatchConditions_s(search_value, len(search_value), alignment, is_float, precision)
        result = self.filter(data_ptr, ctypes.byref(matchConditions), matches)
        self.Process_free_bytes(data_ptr)
        return result

