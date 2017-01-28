import argparse
import os
from struct import *
import subprocess
import shutil
parser = argparse.ArgumentParser(description='Generate Pck archive')
parser.add_argument("Input",help='Input Folder')
parser.add_argument("Output",help='Output Folder')
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
#Long 4bytes
try:
    os.mkdir(args.Output)
except:
    pass
rootDir = os.getcwd()
shutil.copy("WP16.exe",args.Output)
with open(args.Input,'rb+') as fileArchive:
    os.chdir(args.Output)
    numFiles = unpack('L',fileArchive.read(4))[0]
    print numFiles
    fullSize = unpack('L',fileArchive.read(4))[0]
    fileArchive.seek(0x78,1) #seek to end of File header
    for i in range(numFiles):
        tName = fileArchive.read(0x16).rstrip('\0')
        tGroup = unpack('H',fileArchive.read(2))[0]
        tOffset = unpack('L',fileArchive.read(4))[0]
        tZsize = unpack('L',fileArchive.read(4))[0]
        tSize = unpack('L',fileArchive.read(4))[0]
        fileArchiveLastPos = fileArchive.tell()

        
        if tZsize != tSize:
            print "File is compressed: {}, {}, {}".format(tName,tGroup,tZsize)
            with open("temp","wb") as tempFile:
                fileArchive.seek(tOffset)
                tempFile.write(fileArchive.read(tZsize))
            subprocess.call(["WP16.exe","temp","{}-{}".format(tGroup,tName)])
            os.remove("temp")


        else:
            with open("{}-{}".format(tGroup,tName),'wb') as outFile:
                print "File is uncompressed: {}, {}, {}".format(tName,tGroup,tZsize)   
                fileArchive.seek(tOffset)
                outFile.write(fileArchive.read(tZsize))

        fileArchive.seek(fileArchiveLastPos)
        fileArchive.seek(0x5c,1)
os.remove("WP16.exe")

