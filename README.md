# Rampage
Linux memory scanner/editor written in python. Similar to scanmem, artmoney, or cheat engine in concept. Allows you to find values of programs in RAM and then change them. Made to be used inside of a python shell. You don't need to know python to use this, but it can help with some automation.

## Installing

Depends on the custom scanning library written in C - see cscan folder.

1. Build cscan

    ```
    cd cscan
    make
    cd ..
    ```

3. (Optional) compile the demo app

    ```
    cd demo
    make
    ```

## Usage

Launch a program you want to scan, find its pid and figure out what value you want to edit. The demo program conviniently provides all of the above. The demo program will exit if it detects the value being changed to 0xDEADBEEF.

```
>>> Process.find('Test')
10702 TestApp
>>> p = Process(10702)
>>> help(p) # read more! Press 'q' to return back to this shell
>>> p.scan(12) # scan(value): finds instances of value in memory, returns match count
[OK]
6
>>> # Now go to TestApp (or your game) and change the value.
>>> p.scan(0) # In the TestApp new value happened to be 0
[OK]
1
>>> p.get_matches() # returns a list of all matches (here - list of one)
[<Match 0x7ffdbb9680fc - 0 in <MemorySegment6 [stack]>>]
>>> mm.add('test_value', p) 
>>> mm.matches['test_value']
>>> mm.matches['test_value'].value = 0xDEADBEEF # write 0xdeadbeef into the proper location
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/hexorg/Workspace/CS/Rampage/rampage/match.py", line 206, in value
    data = struct.pack(self.fmt, v)
struct.error: ubyte format requires 0 <= number <= 255
>>> # What's this?! The number we provided is larger than 255. The values we searched for
>>> # were really small - 12, and 0. Rampage tries to guess maximum value based on the values
>>> # we looked for. Since maximum value we looked for was less than 255, rampage set 255 as the 
>>> # maximum. If you write more bytes than the target program assumes are there, you will likely
>>> # overwrite some other value and possibly crash the target program. 
>>> # Luckly we know that TestApp uses an integer for its value, so we can safely say
>>> mm.matches['test_value'].fmt = '@I'
>>> help(mm.matches['test_value']) # See help for more info on types
>>> mm.matches['test_value'].value = 0xDEADBEEF
>>> # Now works! In test app you can press [enter] to quit.
```

### MatchManager

The most common task in rampage-like tools is freezing values - if you find your health value you can freeze it to anything you want. MatchManager (mm) already provides freezing functionality

```
>>> # assuming mm already has a match named 'health'
>>> help(mm.freeze) # read this to find the order of arguments, press 'q' to exit help
>>> mm.freeze('health', 100) # Every 1 second, set our health to 100
```

MatchManager also lets you save discovered matches to a file, or load from one. However keep in mind that most games will likely allocate variables at different addresses once the game is restarted. Remember to read help() on Rampage's objects and methods to find more fetures and how to use them!