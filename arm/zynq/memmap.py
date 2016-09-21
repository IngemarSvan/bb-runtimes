#! /usr/bin/env python

import xml.etree.ElementTree as ET

tree = ET.parse('memmap.xml')
root = tree.getroot()

# Translation table (initially empty)
tt = [None for x in range(4096)]

pagealign = 1 << 20


def parse_addr(str):
    ustr = str.upper()
    if ustr.startswith("0X"):
        return int(ustr, 16)
    elif ustr.endswith("GB"):
        return int(ustr[:-2]) << 30
    elif ustr.endswith("MB"):
        return int(ustr[:-2]) << 20
    elif ustr.endswith("KB"):
        return int(ustr[:-2]) << 10
    else:
        return int(ustr)

for child in root:
    name = child.attrib['name']
    addr = parse_addr(child.attrib['base'])
    size = parse_addr(child.attrib['size'])
    if (addr % pagealign) != 0:
        print "base of %s is not aligned" % name
        exit(1)
    addr = addr / pagealign
    if (size % pagealign) != 0:
        print "size of %s is not aligned" % name
        exit(1)
    size = size / pagealign

    cache = child.attrib['cache']
    if cache == 'cb':
        tex = 7
        c = 1
        b = 1
    elif cache == 'nc':
        tex = 0
        c = 0
        b = 1
    else:
        print "unhandled cache attribute '%s' for region %s" % (cache, name)
        exit(1)

    access = child.attrib['access']
    if access == "rwxrwx":
        ap = 3
        nx = 0
    elif access == "rw-rw-":
        ap = 3
        nx = 1
    else:
        print "unhandled access '%s' for region %s" % (access, name)
        exit(1)
    ns = 0
    nG = 0
    S = 1
    domain = 0

    for i in range(addr, addr + size):
        if tt[i]:
            print "overlap at %s in region %s" % (hex(i * pagealign), name)
            exit(1)
        val = ((i << 20) + (ns << 19) + (nG << 17) + (S << 16) +
               (((ap >> 2) & 1) << 15) + (tex << 12) + ((ap & 3) << 10) +
               (domain << 5) + (nx << 4) + (c << 3) + (b << 2) + 2)
        tt[i] = {'name': name,
                 'format': 'section', 'base': i, 'ns': ns,
                 'nG': nG, 'S': S, 'AP': ap, 'TEX': tex, 'domain': domain,
                 'XN': nx, 'C': c, 'B': b, 'val': val}
#    print name, addr, size
#    print child.tag, child.attrib

addr = 0
for e in tt:
    if e:
        v = e['val']
        n = e['name']
    else:
        v = 0
        n = "*none*"

    print "\t.long 0x%08x  @ for 0x%08x, %s" % (v, addr, n)
    addr += pagealign