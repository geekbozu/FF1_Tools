## "Special" file depacker/repacker for geekboy1011
## Coffeeright 2017 Rodger "Iambian" Weisman

import time,os,sys,ctypes,struct
np,se,bn,cd = (os.path.normpath,os.path.splitext,os.path.basename,os.getcwd())
FILES_PROCESSED = 0
FILES_DEPACKED = 0
ENABLE_FASTMODE = 0
NO_COMPRESS = False
QUIET_MODE = False

# ===========================================================================
# haha.

def usage():
  print ""
  print "usage: "+bn(__file__)+" in_file out_file [-r] [-f] [-n] [-q]"
  print " in_file: File (if unpacking) or folder (if repacking)"
  print "out_file: Folder (if unpacking) or file (if repacking)"
  print "      -r: Specify this to switch from unpack to repack"
  print "      -f: Specify this to use faster but less effective compression method"
  print "      -n: Specify this to leave everything uncompressed"
  print "      -q: Specify to enable disable progress text output"


# ===========================================================================
# Miscellaneous

def ensure_dir(d):
    if not os.path.isdir(d): os.makedirs(d)
    
def emitfile(basepath,filename,data):
  global FILES_PROCESSED
  global QUIET_MODE
  FILES_PROCESSED+=1
  outfilename = np(basepath)+'/'+filename
  if len(outfilename)>65:
    s = "..."+outfilename[-65:]
  else:
    s = outfilename+' '*(65-len(outfilename)+3)
  if not QUIET_MODE: print "Emitting "+s+"\r",
  outfile = open(outfilename,'wb')
  outfile.write(data)
  outfile.close()

# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Wp16 compressor/decompressor

if os.name == 'nt':
#  if not os.path.isfile('Wp16e.dll')
  if 4==ctypes.sizeof(ctypes.c_void_p):
    wp16lib = ctypes.CDLL('tools\\Wp16e.dll')
  else:
    wp16lib = ctypes.CDLL('tools\\Wp16e64.dll')
else:
  # might require LD_LIBRARY_PATH set
  wp16lib = CDLL("libWp16e.so")
def pack(src,fastmode=0):
  slen = len(src)//2
  if slen<=0: raise ValueError('Invalid input.')
  clen = wp16lib.get_max_compressed_size(slen)
  dst = ctypes.create_string_buffer(clen*2)
  clen = wp16lib.compress(src,slen,dst,fastmode)
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
  wp16lib.decompress(src,len(src)/2,dst,0)
  return dst[0:dlen*2]
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Implementing a memoryfile class

class memfile():
  def __init__(self,s=''):
    self.s = s
    self.fp = 0
    self.mode = 'rb+'
  def read(self,b=0):
    a = len(self.s)
    if not b: b=a-self.fp
    if b+self.fp>a: b=a-self.fp
    c = self.s[self.fp:self.fp+b]
    self.fp+=b
    return c
  def write(self,s):
    a = len(self.s)
    sl = len(s)
    if a != self.fp:
      self.s = self.s[:self.fp]+s+self.s[self.fp+sl:]
    else:
      self.s+=s
    self.fp += sl
    return
  def tell(self):
    return self.fp
  def seek(self,o,w=0):
    if not w:
      self.fp = o
    elif w==1:
      self.fp += o
    else:
      self.fp = len(self.s)-o
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Depackager/repackager class
# Note: The ONLY reason it's a class is for ease of recursion
    
class fpackage():
  def __init__(self,filehandle):
    if isinstance(filehandle,type('')):
      self.fh = memfile(filehandle)
    else:
      self.fh = filehandle
# ---
  def unpack(self,basepath,filename):
    global FILES_DEPACKED
    fh = self.fh
    fh.seek(0,2)  #seek EoF
    flen = fh.tell()
    fh.seek(0)    #reset to start of file
    fheader = fh.read(128)
    if len(fheader)<128:
#      print "Header mismatch on test. Emitting short file."
      emitfile(basepath,filename,fheader)
      return
    else:
      nfiles  = struct.unpack("L",fheader[0:4])[0]
      arcsize = struct.unpack("L",fheader[4:8])[0]
      if flen != arcsize or flen < 128+nfiles*128:
 #       print "File length mismatch on test. Found "+str(flen)+", got "+str(arcsize)+". Emitting file."
        emitfile(basepath,filename,fheader+fh.read())
        return
      fstruct = dict()
      newpath = np(basepath+'/'+filename+'/')
      ensure_dir(newpath)
      for i in xrange(nfiles):
        obj   = fh.read(128)
        fptr  = fh.tell()
        aName = obj[0:0x16].rstrip('\0')
        aSeri = struct.unpack("H",obj[0x16:0x18])[0]
        aOffs = struct.unpack("L",obj[0x18:0x1C])[0]
        aRSiz = struct.unpack("L",obj[0x1C:0x20])[0]
        aCSiz = struct.unpack("L",obj[0x20:0x24])[0]
        nname = format(aSeri,'04x')+'-'+aName
        fh.seek(aOffs,0)
        aData = fh.read(aRSiz)
        if aRSiz!=aCSiz and aData[0:4]=="Wp16":
          FILES_DEPACKED+=1
          #print "Depacking "+aName+" of length "+str(len(aData))
          aData = depack(aData)
          if len(aData)>aCSiz:
            aData = aData[:aCSiz]
        t = fpackage(aData)
        t.unpack(newpath,nname)
        fh.seek(fptr,0)
# ---
  #Note: Individual files are not compressed. Only folders.
  def repack(self,basepath):
    global FILES_PROCESSED
    global ENABLE_FASTMODE
    global NO_COMPRESS
    global QUIET_MODE
    pathlist = os.listdir(np(basepath))
    fh = self.fh
    fh.seek(0) #rewind
    fh.write(''.join(['\0']*(0x80*(len(pathlist)+1))))  #dummy out SoF for headers
    curhptr = 0x80
    curdptr = fh.tell()
    headers = []  #contains lists [name,serial,rawsiz,cmpsiz,offset]
    for i in pathlist:
      filepath = np(basepath+'/'+i)
      if os.path.isdir(filepath):
        if not QUIET_MODE: print "Directory found: "+i
        t = fpackage("")
        t.repack(filepath)
       # print t.fh.__dict__
        f = t.fh
        f.seek(0)    #reset to start of file
        s = f.read() #get file contents
        rawlen = len(s) + (-len(s)%0x80) ## SIZE PADDING FIX
        if NO_COMPRESS:
          cmplen = rawlen
        else:
          s = pack(s,ENABLE_FASTMODE)
          cmplen = len(s)+8 + (-(len(s)+8)%0x80) ## SIZE PADDING FIX
          s = "Wp16"+struct.pack("L",rawlen)+s
        if not QUIET_MODE: print "Directory "+i+" packaged to "+str([rawlen,cmplen])+" bytes"
      else:
        f = open(filepath,"rb")
        s = f.read()
        rawlen = len(s) + (-len(s)%0x80) ## SIZE PADDING FIX
        cmplen = rawlen
        if not QUIET_MODE: print "File "+i+" of length "+str(cmplen)+" bytes found."
        FILES_PROCESSED+=1
      serial = int(i[0:4],16)
      if len(i)<5 or i[4]!='-':
        raise RuntimeError("File name"+i+" invalid at "+basepath)
      name = (i[5:]+''.join(['\0']*32))[:0x16]  #zero-pad to or cut off at 0x16 chars
      headers.append([name,serial,rawlen,cmplen,curdptr])
      s += ''.join(['\0']*(-len(s)%0x80))    #zero-pad to next 0x80 boundary
      fh.write(s)
      curdptr = fh.tell()
    # total archive size is equal to curdptr
    # We can now construct the file header.
    fh.seek(0)
    s = struct.pack("L",len(headers))+struct.pack("L",curdptr)+''.join(['\0']*120)
    fh.write(s)  #write package header
    headers.sort(key=lambda x: x[4])  #sort by nearest current displacement
    for v in headers:
      s=v[0]
      s+=struct.pack("H",v[1])
      s+=struct.pack("L",v[4])
      s+=struct.pack("L",v[3])  #Actual object size (compressed)
      s+=struct.pack("L",v[2])  #Size prior to compression if compressed
      s+=''.join(['\0']*92)     #zero-padding
      fh.write(s)
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# Main

if __name__ == '__main__':
  start_time = time.time()
  if len(sys.argv)<3:
    usage()
    sys.exit(1)
  infp  = sys.argv[1]
  outfp = sys.argv[2]
  if '-f' in sys.argv[3:]:
    ENABLE_FASTMODE=1
  else:
    ENABLE_FASTMODE=0
  if '-n' in sys.argv[3:]:
    NO_COMPRESS = True
  else:
    NO_COMPRESS = False
  if '-q' in sys.argv[3:]:
    QUIET_MODE = True
  else:
    QUIET_MODE = False
    
    
  if '-r' in sys.argv[3:]:
    ## --- Start app in repackager mode
    _=fpackage(open(outfp,'wb+'))
    _.repack(infp)
    _.fh.seek(0,2)
    print "Files processed: "+str(FILES_PROCESSED)
    print "Total filesize : "+str(_.fh.tell())
  else:
    ## --- Start app in unpacking mode
    _=fpackage(open(infp,"rb"))
    _.unpack(outfp,'')
    print "\n"
    print "Files emitted  : "+str(FILES_PROCESSED)
    print "Files depacked : "+str(FILES_DEPACKED)
  print "Time elapsed : "+str(round(time.time() - start_time,3))+" seconds"


   
'''
start_time = time.time()
t = fpackage(open("_in/crown.dpk","rb"))
t.unpack("_out","crown.dpk")
print "\nTime elapsed : "+str(round(time.time() - start_time,3))+" seconds"
print "Files emitted  : "+str(FILES_PROCESSED)
print "Files depacked : "+str(FILES_DEPACKED)

print "Packing..."
start_time = time.time()
t = fpackage(open("_ptst/testio.dpk","wb+"))
t.repack("_ptst/test.dpk")
t.fh.seek(0,2)  #EOF
print "\nTime elapsed : "+str(round(time.time() - start_time,3))+" seconds"
print "Archive size   : "+str(t.fh.tell())

print "Verifying results via depack:"
start_time = time.time()
t = fpackage(open("_ptst/testio.dpk","rb"))
t.unpack("_ptst","results")
print "\nTime elapsed : "+str(round(time.time() - start_time,3))+" seconds"
print "Files emitted  : "+str(FILES_PROCESSED)
print "Files depacked : "+str(FILES_DEPACKED)
'''






















