# Rampage
Linux memory scanner/editor written in python. Similar to scanmem, artmoney, or cheat engine in concept. Allows you to find values of programs in RAM and then change them. 

## Installing

Depends on `python-ptrace`, `hurry.filesizeand` the custom scanning library written in C - see cscan folder. Though if you don't want isntalling `hurry.filesizeand` you can remove it from process.py - it's only used for pretty printing.

1. Install python-ptrace

    ```
    pip install python-ptrace hurry.filesizeand
    ```

2. Install cscan

    ```
    cd cscan
    python setup.py install
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
>>> p.attach()
Process has 315KB of scannable memory
>>> p.scan(12) # scan(value): finds instances of value in memory, returns match count
7/7: Searching <MemorySegment [stack]> ... 2 matches 35MB/s
6
>>> p.scan(1804289383) # demo app sets value to random numbers, likely only 2 scans needed
1
>>> m = p.get_matches() # returns a list of all matches (here - list of one)
>>> m.update() # for all matches in the list - re-reads those values
>>> m
[<Match 0x7ffbffffaecc - 846930886 in <MemorySegment [stack]>>]
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

### Optimizing search

Search speed depends on your CPU, size of the program you are targetting, what kind of values you're looking for, and what kind of memory segments are there. Luckly, `Process.scan()` lets you configure most of those options. Let's look at its signature:

```
    def scan(self, value, memorySegments=None, search_types=['@c', '@B', '@h', '@H', '@i', '@I', '@l', '@L', 'f', 'd'], alignment=4)
```

* **value** - the value to be searched, can be anything as long as it can be expressed as one of the search_types
* **memorySegments** - list of MemorySegment objects to search, or None to use all writable memory. Segments must actually be mapped by this process. Useful if you know that your value is likely in a certain segment (e.g. heap). Use `Process.map.find(addressOrPath)` or manually sift through `Process.map.segments` to build this list. 


* **search_types** - list of raw types to search. Any value usable by `struct` can be used. See https://docs.python.org/3.6/library/struct.html
* **alignment** - only search byte aligned values. Increases search speed by this factor, but has a chance to miss values in some programs. On my desktop I scan at 12MB/s with alignment=1, 55MB/s with alignment=4. Most modern compilers compile 4- or 8- byte aligned data, so using 4 gives us a good chance. 