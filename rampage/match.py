import struct, ctypes
import time
import json
import threading

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




class MatchManager(threading.Thread):
    '''
    A class to manage matches that you want to keep.
    '''
    def __init__(self):
        super().__init__()
        self.__matches__ = {}
        self.__frozen__ = {}
        self.start()
    
    def __repr__(self):
        return f"<{self.__class__.__name__} - {len(self.__matches__)} match{'es' if len(self.__matches__)>1 else ''}>"
    
    def add(self, name, match):
        '''
        Keep track of a match and give it a name.
        Can accept Process object instead of a match - will use the first match in
        the Process. E.g. once p.scan() finds only one match, simply do
        MemoryManager.add('health', p) as a shortcut of MemoryManager.add('health', p.get_matches[0])

        Parameters:
            name (string) - name this match, e.g. 'gold', 'health'
            match (MemoryMatch or Process) - the match to store or get the first match from the process.
        '''
        if isinstance(match, MemoryMatch):
            self.__matches__[name] = match
        else:
            self.__matches__[name] = match.get_matches()[0]
    
    def manual_add(self, name, address, process):
        '''
        Manually create a match by specifying its address.

        Parameters:
            name (string) - name this match, e.g. 'gold', 'health'
            address (int) - memory address of this match
            process (Process) - which process this match belongs to.
        '''
        segment = process.map.find(address)
        if segment is None:
            raise Exception("Given address is not mapped by the process")
        m = MemoryMatch(segment, address-segment.start)
        self.add(name, m)
        return m

    
    def clear(self):
        '''
        Remove all matches.
        '''
        self.__matches__.clear()
    
    @property
    def matches(self):
        '''
        Return dict of all saved matches. Can be used to do tasks of a single match
        E.g. MatchManager.matches['health'].value = 100
        '''
        return self.__matches__
    
    def freeze(self, name, value, condition=None):
        '''
        Set this {name} match to value every second if condition is met.

        Parameters:
            name (string) - name of the match, same as used in add()
            value (int or float) - what value to set this variable to. 
            condition (lambda v) - Default unconditional. Only change value if the condition is met.
                Condition must return True when the match must be set to value. Useful if you want
                to top off your gold if its low, but keep it unfrozen otherwise.
        '''
        if name in self.__matches__:
            self.__frozen__[name] = (value, condition)
        else:
            raise KeyError(f"Unknown match '{name}'")
    
    def unfreeze(self, name):
        '''
        Stop freezing the match stored under name.

        Parameters:
            name (string) - name of the match, same as used in add()
        '''
        return self.__frozen__.pop(name)
    
    def save(self, filepath):
        '''
        Save currently stored matches to a file for later use.
        There is a high chance that if you restart the game process, 
        variable addresses will change.
        '''
        with open(filepath, 'w') as f:
            json.dump(self, f, cls=JSONMatchEncoder)
    
    @staticmethod
    def load(filepath, process):
        '''
        Load stored matches for a file

        Parameters:
            filepath (string) - Path to the file previously saved with save()
            process (Process) - Process of the game the matches are for.
        '''
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
        '''
        This routine runs in a separate thread and performs the actual freezing of values.
        You don't need to call this. Separate thread is started for you.
        '''
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
    '''
    A convinience class to manage multiple matches.
    '''
    def set(self, value):
        '''
        Set all matches in this list to the value specified
        '''
        for match in self:
            match.value = value

class MemoryMatch:
    '''
    A match of a single address in game's memory. Types are specified in struct format strings.
    See https://docs.python.org/3.7/library/struct.html for acceptable types.

    To change match type, set MemoryMatch.fmt to the value you want
    '''
    def __init__(self, segment, offset):
        self.segment = segment
        self.offset = offset
        self.fmt = '@i'
    
    def __repr__(self):
        return f"<Match {hex(self.segment.start + self.offset)} - {self.value} in {self.segment}>"

    @property
    def value(self):
        '''
        Current value of this match in game's memory. Always up-to-date.
        '''
        length = struct.calcsize(self.fmt)
        data = self.segment.read_bytes(self.offset, length)
        return struct.unpack(self.fmt, data)[0]

    @value.setter
    def value(self, v):
        '''
        Change current value of this match in the game's memory.
        '''
        data = struct.pack(self.fmt, v)
        self.segment.write_bytes(self.offset, data)
    
    def whats_around(self, lines=8, fmt=None, offset=0):
        '''
        Print a hexdump of values nearby this match. Useful for structured data.
        E.g. if this match is a health value, it's probable that armor will be nearby
        the health value.

        You can use MatchManager.manual_add() to add values discovered through this method.

        Parameters:
            lines (int): Default 8. Print n hexdump lines above and n lines below the current match 
                address.
            fmt (struct format): Default - same as match. Override displayed type. Does not change
                current match's type. If format is 1-byte wide, outputs values in hex, otherwise - decimal.
        '''
        if fmt is None:
            fmt = self.fmt
        
        from .pretty_print import hexdump
        bytes_in_line = 16
        dump_offset = self.offset - bytes_in_line*lines + offset - (self.offset & 0xF)
        dump_size = bytes_in_line+2*bytes_in_line*lines # lines up, lines down, line that I'm on
        whatsThere = self.segment.read_bytes(dump_offset, dump_size)
        hexdump(whatsThere, self.segment.start + dump_offset, fmt)



