import argparse
import os
from struct import pack

parser = argparse.ArgumentParser(description='Generate Pck archive')
parser.add_argument("Input", help='Input Folder')
parser.add_argument("Output", help='Output File')
args = parser.parse_args()
'''
Header
File Table
FileData

Header            | Total Size: 0x80
------------------------------------
FileCount         | Size: 0x4
Archive Size      | Size: 0x4
Padding           | Size: 0x78


File Table  Total | Size: NumFiles*0x80
---------------------------------------
File Name         | Size: 0x16
???               | Size: 0x2         ;Depacker treats this as part of the file name?  Changes on each file
Offset To File    | Size: 0x4         ;From Archive Start
Size in Archive   | Size: 0x4
Uncompressed Size | Size: 0x4         ;If file is a compressed stream these will differ.
Padding           | Size 0x5C

FileData          | Total Size:  ArchiveSize-FileTable-Header
Appended to the table is the stream of all assets marked out by earlier files.
'''

FileMetaData = []

for i in os.listdir(args.Input):
    # with open('{}/{}'.format(args.Input, i)) as f:
    rID, name = i.split('-')
    size = os.stat('{}/{}'.format(args.Input, i)).st_size
    FileMetaData.append([name, size, 0, rID])
    print('{}|{}|{}|{}'.format(name, size, 0, rID))
# Name | Size | Offset | Resource ID

NumFiles = len(FileMetaData)
OFS = (NumFiles+1)*0x80

previousFileSize = 0
for i in FileMetaData:
    i[2] = OFS+previousFileSize
    OFS = i[2]
    previousFileSize = i[1]
    FullSize = i[2]+previousFileSize

with open(args.Output, 'w+b') as f:
    f.write(pack('L', NumFiles))
    f.write(pack('L', FullSize))
#    array('L', NumFiles).tofile(f)
#    array('L', FullSize).toFile(f)
    f.seek(0x78, 1)
    for i in FileMetaData:
        saveOFS = f.tell()
        f.write(i[0])
        f.seek(saveOFS)
        f.seek(0x16, 1)
        f.write(pack('H', int(i[3])))
        f.write(pack('L', i[2]))
        f.write(pack('L', i[1]))
        f.write(pack('L', i[1]))
        f.seek(0x5C, 1)

    for i in FileMetaData:
        with open('{}/{}-{}'.format(args.Input, i[3], i[0]), 'rb') as t:
                f.write(t.read())
