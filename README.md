# Rampage
Linux memory scanner/editor written in python. Similar to scanmem, artmoney, or cheat engine in concept. Allows you to find values of programs in RAM and then change them. 

## Installing

Depends on python-ptrace and the custom scanning library written in C - see cscan folder.

1. Install python-ptrace

    ```
    pip install python-ptrace
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
>>> p.scan(12) # scan(value): finds instances of value in memory, returns match count
8368
>>> p.scan(1804289383) # demo app sets value to random numbers, likely only 2 scans needed
1
>>> m = p.get_matches() # returns a list of all matches (here - list of one)
>>> m.update() # for all matches in the list - re-reads those values
>>> m
[<Match 0x7ffbffffaecc - 846930886 in <MemorySegment [stack]>>]
>>> m.set(0xdeadbeef) # write 0xdeadbeef into the proper location
```
