import struct, ctypes
import time
import json

class JSONMatchEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, MemoryMatch):
            return {'address': o.segment.start + o.offset, 'type': o.fmt}
        if isinstance(o, MatchManager):
            return {'matches': o.__matches__}
        else:
            super().default(o)

def jsonDecoder(dictionary):
    if 'matches' in dictionary:
        mm = MatchManager()
        mm.__matches__ = dictionary['matches']
        return mm
    if 'address' in dictionary and 'type' in dictionary:
        mm = MemoryMatch(None, dictionary['address'])
        mm.fmt = dictionary['type']
        return mm
    return dictionary




class MatchManager():
    def __init__(self):
        super().__init__()
        self.__matches__ = {}
        self.__frozen__ = {}
    
    def __repr__(self):
        return f"<{self.__class__.__name__} - {len(self.__matches__)} match{'es' if len(self.__matches__)>1 else ''}>"
    
    def add(self, name, match):
        if isinstance(match, MemoryMatch):
            self.__matches__[name] = match
        else:
            self.__matches__[name] = match.get_matches()[0]
    
    def manual_add(self, name, address, process):
        segment = process.map.find(address)
        if segment is None:
            raise Exception("Given address is not mapped by the process")
        m = MemoryMatch(segment, address-segment.start)
        self.add(name, m)
        return m

    
    def clear(self):
        self.__matches__.clear()
    
    def get(self, key):
        return self.__matches__[key]
    
    @property
    def matches(self):
        return self.__matches__
    
    def set(self, name, value, fmt='@i'):
        self.__matches__[name].set(value, fmt)
    
    def update(self, name, fmt='@i'):
        return self.__matches__[name].update(fmt)
    
    def freeze(self, name, value, condition=None):
        '''
        Set this {name} match to value every second if condition is met.
        '''
        if name in self.__matches__:
            self.__frozen__[name] = (value, condition)
        else:
            raise KeyError(f"Unknown match '{name}'")
    
    def unfreeze(self, name):
        return self.__frozen__.pop(name)
    
    def save(self, filepath):
        with open(filepath, 'w') as f:
            json.dump(self, f, cls=JSONMatchEncoder)
    
    @staticmethod
    def load(filepath, process):
        with open(filepath, 'r') as f:
            mm = json.load(f, object_hook=jsonDecoder)
            for match in mm.__matches__:
                address = mm.__matches__[match].offset
                segment = process.map.find(address)
                if segment is None:
                    print(f"Warning: loaded match at {hex(address)} isn't mapped by this process")
                else:
                    mm.__matches__[match].segment = segment
                    mm.__matches__[match].offset = address - segment.start
            return mm


    def run(self):
        isInterrupted = False
        while not isInterrupted:
            for key in self.__frozen__:
                value, condition = self.__frozen__[key]
                is_set = True
                if condition is not None:
                    is_set = condition(self.__matches__[key].value)
                if is_set:
                    self.__matches__[key].value = value
            try:
                time.sleep(1)
            except KeyboardInterrupt as e:
                isInterrupted = True
    



class Matches(list):
    def set(self, value, fmt=None):
        for match in self:
            match.set(value, fmt)
    
    def update(self, fmt=None):
        for match in self:
            match.update(fmt)

class MemoryMatch:
    def __init__(self, segment, offset):
        self.segment = segment
        self.offset = offset
        self.fmt = '@i'
    
    def __repr__(self):
        return f"<Match {hex(self.segment.start + self.offset)} - {self.value} in {self.segment}>"

    @property
    def value(self):
        length = struct.calcsize(self.fmt)
        data = self.segment.read_bytes(self.offset, length)
        return struct.unpack(self.fmt, data)[0]

    @value.setter
    def value(self, v):
        data = struct.pack(self.fmt, v)
        self.segment.write_bytes(self.offset, data)
    
    def whats_around(self, lines=8, fmt=None, offset=0):
        if fmt is None:
            fmt = self.fmt
        
        from .pretty_print import hexdump
        bytes_in_line = 16
        dump_offset = self.offset - bytes_in_line*lines + offset - (self.offset & 0xF)
        dump_size = bytes_in_line+2*bytes_in_line*lines # lines up, lines down, line that I'm on
        whatsThere = self.segment.read_bytes(dump_offset, dump_size)
        hexdump(whatsThere, self.segment.start + dump_offset, fmt)



