# Rampage
Linux memory scanner/editor written in python. Similar to scanmem, artmoney, or cheat engine in concept. Allows you to find values of programs in RAM and then change them. 

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
>>> from rampage.interface.process import Process
>>> p = Process(pid)
Process has 315.392KB of scannable memory
>>> p.scan(12) # scan(value): finds instances of value in memory, returns match count
7/7: Searching <MemorySegment6 [stack]> ... 2 matches 217.925MB/s
6
>>> p.scan(1804289383) # demo app sets value to random numbers, likely only 2 scans needed
1
>>> m = p.get_matches() # returns a list of all matches (here - list of one)
>>> m.update() # for all matches in the list - re-reads those values
>>> m
[<Match 0x7ffbffffaecc - 846930886 in <MemorySegment6 [stack]>>]
>>> m.set(0xdeadbeef) # write 0xdeadbeef into the proper location
```

### Freezing values

The most common task similar tools are used for is freezing values - if you find your health value you can freeze it to anything you want. This is where having a python shell comes very usefull simply

```
>>> # assuming m already has a match
>>> import time
>>> while True:
>>>     if m.update() < 50: # once your health drops below 50
...         m.set(100) # heal yourself
...     time.sleep(1.0) # check once per second

```