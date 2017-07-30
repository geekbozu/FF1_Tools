''' This file is part of FF1DS_PK which is released under the MIT License.
    See LICENSE for full license details.                                  '''

import time
import os
import sys
import ctypes
import re
import subprocess

print "---------------------------------------------"
print "Loading files..."


#=============================================================================
def readFile(file):
    a = []
    f = open(file,'rb')
    b = f.read(1)
    while b!=b'':
        a.append(ord(b))
        b = f.read(1)
    f.close()
    return a

def writeFile(file,a):
    f = open(file,'wb+')
    f.write(bytes(a))
    f.close()

def ensure_dir(d):
    if not os.path.isdir(d):
        os.makedirs(d)
    return

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Wp16c compressor/decompressor
if os.name == 'nt':
#  if not os.path.isfile('Wp16e.dll')
  if 4==ctypes.sizeof(ctypes.c_void_p):
    wp16lib = ctypes.CDLL(os.path.dirname(__file__)+'\\Wp16e.dll')
  else:
    wp16lib = ctypes.CDLL(os.path.dirname(__file__)+'\\Wp16e64.dll')
else:
  # might require LD_LIBRARY_PATH set
  wp16lib = CDLL("libWp16e.so")
def pack(src,fastmode=0):
  slen = len(src)//2
  if slen<=0: raise ValueError('Invalid input.')
  clen = wp16lib.get_max_compressed_size(slen)
  dst = ctypes.create_string_buffer(clen*2)
  print "Maximum allowed len: "+str(clen*2)
  clen = wp16lib.compress(src,slen,dst,fastmode)
  print "Output length at :"+str(clen*2)
  if clen<0: raise MemoryError('Compressor ran out of memory to malloc')
  return dst[0:clen*2]
#  buffer(dst,0,dlen*2)
def depack(src):
  if src[0:4]!="Wp16": raise ValueError('Invalid header.')
  dlen = wp16lib.get_decomp_size(src,len(src)/2,4)
  dst = ctypes.create_string_buffer(dlen*2)
  wp16lib.decompress(src,len(src)/2,dst,4)
  return dst[0:dlen*2]
def depackraw(src):
  dlen = wp16lib.get_decomp_size(src,int(len(src)/2),0)
  dst = ctypes.create_string_buffer(dlen*2)
  print "Length of depacked: "+str(len(dst))
  wp16lib.decompress(src,len(src)/2,dst,0)
  return dst[0:dlen*2]
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-

  
## --- Begin test procedure ---
print "---------------------------------------------"
start_time = time.time()
in_file = open("../OLD_TESTS/796-AIRSHIP.PCK","rb")
in_arr = in_file.read()
print "Type of in_arr:"+str(type(in_arr))
print "Size of input file: "+str(len(in_arr))
comp_arr = pack(in_arr)
#comp_arr_2 = "".join(x for x in comp_arr)
print "Size of cmpr array: "+str(len(comp_arr))
print "Type of comp_arr:"+str(type(comp_arr))
decomp_arr = depackraw(comp_arr)
print "Size of cmpr array: "+str(len(comp_arr))
print "Verifying files..."
ver_failed = False
for i in range(min(len(in_arr),len(decomp_arr))):
  if in_arr[i]!=decomp_arr[i]:
    print "File mismatch at position [%i]" % (i,)
    ver_failed = True
if ver_failed:
  print "Files are mismatched."
else:
  print "Files are identical."
print "Time elapsed: "+str(time.time() - start_time)









