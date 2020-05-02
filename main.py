
from rampage.interface.process import Process

if __name__ == '__main__':
    import sys
    pid = sys.argv[1]

    p = Process(pid)
    p.attach()
    seg = [p.maps.segments[0]]
    matches = p.scan(187, seg)
    print(f"Found {len(matches)} matches")

