''' This file is part of FF1DS_PK which is released under the MIT License.
    See LICENSE for full license details.                                  '''

import sys,os,getopt

BACKREF_DIST = 2**11-1
MAXCODELEN   = 2**5-1+2

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
#-----------------------------------------------------------------------------
def writeFile(file,a):
        f = open(file,'wb+')
        f.write(bytes(a))
        f.close()
#-----------------------------------------------------------------------------
def puts(val):
  print val
#-----------------------------------------------------------------------------
def usage():
  print "WP16 (de)compression implementation"
  print "------------------------------------"
  print "usage: wp16 -i <infile> [-o <outfile>] [-d]"
  print "-i <infile>   : Input filename (with extension) "
  print "-o <outfile>  : Output filename (with extension)"
  print "                If excluded, runs in test mode"
  print "-d            : Decompresses instead of compress"
#-----------------------------------------------------------------------------
''' Compressed file format:
[0:4]           = "Wp16"
[4:8]           = 32-bit filesize in bytes (little-endian)
[n:n+4]         = 32-bits flags (1=literal 0=backref)
[n+4:n+4+(32*2) = Data words.
         backref: [dddddddd dddccccc] d=distance (words) c=count (c+2)
              ex: c=3 d=5 repeats last 10 bytes
            note: dmax= 2047, cmax = 31+2
'''
def compress(inarray):
  global MAXCODELEN
  global BACKREF_DIST
  # --- Functions
  def flush(outarr):
    if emit.arr32:
      outarr.append(emit.flags)
      outarr.extend(emit.arr32)
    emit.arr32 = []
    emit.fcount = 0
    #print "FLG "+str(format(emit.flags,'08X'))
    emit.flags = 0
    #sys.exit(2)
  def emit(outarr,backref_or_literal,count=0):
    if count:
      # print "Emitting: "+str([backref_or_literal,count])
      if count<2:
        raise ValueError("Count not allowed to be less than 2 before emitting")
      emit.arr32.append((backref_or_literal<<5)+count-2)
    else: #If count was 0, emit as literal
      emit.arr32.append(backref_or_literal)
      emit.flags |= 1<<emit.fcount
    emit.fcount+=1
    if emit.fcount>31:
      flush(outarr)
  emit.flags  = 0
  emit.fcount = 0
  emit.arr32 = []
  # --- Initializations
  a = []  #input data list (in words)
  o = []  #output data list (flags:32words)
  lbhptr = 0    #filestart
  cptr = 1      #filestart+1
  if not len(inarray): return puts("Err: Cannot compress empty file")
  # --- Converts byte list to word list
  for i,v in enumerate(inarray):
    if i%2: a.append(v*256+t)
    else: t = v
  # print [format(i,'04x') for i in a]
  if len(inarray)%2: a.append(t)
  emit(o,a[0])  #Always emit first byte as a literal
  # --- Outer loop. Continues until no more words can be read in
  while True:
    
    if not cptr%1000:
      print str(cptr)+" of "+str(len(a))
    f_len = -1
    f_ptr = 0
    # -- Begin scanning starting at the back of the window to cur pointer
    for i in range(max(0,cptr-BACKREF_DIST),cptr):
      # -- Scan inside up to maxlen if there are any matches.
      t_len = 0
      t_cptr = cptr
      for j in xrange(i,min(i+MAXCODELEN,len(a))-1):
        if a[j]==a[t_cptr]:
          t_cptr+=1
          t_len+=1
          if t_cptr==MAXCODELEN or t_cptr>=len(a):
            break
        else:
          break
      if t_len>1 and t_len>f_len:
        f_len = t_len
        f_ptr = i
    # -- Nothing was found. Emit literal, increment cptr
    if f_len<2:
      #print "LIT "+str(a[cptr])
      emit(o,a[cptr])
      cptr+=1
    # -- Match found. Put in backref and advance cptr by count
    else:
      #print "LZC "+str(cptr)+","+str(f_len)
      emit(o,cptr-f_ptr,f_len)
      #print "Match at "+str(cptr)+" of len "+str(f_len)
      cptr+=f_len
    # -- Exit if cptr equal to array len. If greater than, error out. something went wrong
    if cptr>=len(a):
      flush(o)
      break
  # --- Convert output list to byte array
  c = 0
  d = []
  # print [format(i,'04x') for i in o]
  for i in o:
    d.append((i>>0)&0xFF)
    d.append((i>>8)&0xFF)
    if not c:
      d.append((i>>16)&0xFF)
      d.append((i>>24)&0xFF)
    c=(c+1)%33
  # print [format(i,'02x') for i in d]
  m = ['W','p','1','6']
  i = len(inarray)
  # print "Output array length: "+str(i)
  m += [ (i>>0)&0xFF,(i>>8)&0xFF,(i>>16)&0xFF,(i>>24)&0xFF ]
  # print "Output array header: "+str(m)
  return m + d
#-----------------------------------------------------------------------------
''' Compressed file format:
[0:4]           = "Wp16"
[4:8]           = 32-bit filesize in bytes (little-endian)
[n:n+4]         = 32-bits flags (1=literal 0=backref)
[n+4:n+4+(32*2) = Data words.
         backref: [dddddddd dddccccc] d=distance (words) c=count (c+2)
              ex: c=3 d=5 repeats last 10 bytes
            note: dmax= 2047, cmax = 31+2
'''
def decompress(inarray):
  print inarray[0:4]
  if inarray[0:4] != [ord('W'),ord('p'),ord('1'),ord('6')] or len(inarray)<14:
    print "Error: Archive header invalid"
    return
  a = inarray[4:8]
  print [format(i,'02x') for i in a]
  fsize = a[0]+a[1]*256+a[2]*65535+a[3]*16777216
  # -- Arbitrary safeguard to prevent ridiculous values
  if fsize>2**30:
    print "Warning/Error: Output size exceeds 1GB. Possible encode error."
    return
  # -- Convert binary input array to codeword array
  # print [format(i,'02x') for i in inarray[4:len(inarray)]]
  cptr = 8
  iter = 0 #0f 33, 0 being codeword section
  b = []
  # print inarray[cptr]+inarray[cptr+1]*256
  while cptr<(len(inarray)):
    t = inarray[cptr+0]
    t += inarray[cptr+1]*256
    cptr+=2
    if not iter:
      # t*=65536
      # t += inarray[cptr+0]
      # t += inarray[cptr+1]*256
      t += inarray[cptr+0]*65536
      t += inarray[cptr+1]*16777216
      cptr+=2
    b.append(t)
    iter=(iter+1)%33
  # print [format(i,'04x') for i in b]
  # -- Read from codeword array and start decompressing
  cptr = 2048
  iter = 0
  flags = 0
  c = [0x00] * 2048
  for i in b:
    if not iter:
      #print "FLG "+str(format(i,'08x'))
      flags=i
    else:
      if flags%2:
        #print "LIT "+str(format(i,'04x'))
        c.append(i)
        cptr+=1
      else:
        coun = (i&0x1F)+2
        bref = (i>>5)&0x7FF
        if bref == 0:
          bref = 0x0800
        #print "LZC "+str([i,cptr,bref,len(c)])
        for j in range(cptr-bref,cptr-bref+coun):
          c.append(c[j])
        cptr+=coun
      flags >>= 1
    iter=(iter+1)%33
  c = c[2048:]
  print "Iteration stopped at "+str(iter)
  # --- Convert word list to byte list
  b = []  #Frees up memory
  d = []  #Init for last section
  for i in c:
    d.append(i&0xFF)
    d.append((i>>8)&0xFF)
  if len(d)!=fsize:
    if fsize==len(d)-1:
      d.pop()  #remove last byte since infile does isn't even.
    else:
      print "Error: Output decompression array does not match expected size"
      print "Expected filesize: "+str(fsize)
      print "File returned    : "+str(len(d))
  return d
  
  
#=============================================================================
# Standalone
if __name__ == '__main__':
  print "Loading objects..."
  #---------------
  try:
    opts,args = getopt.gnu_getopt(sys.argv,"hi:o:d")
  except getopt.GetoptError:
    usage()
    sys.exit(2)
  #---------------
  decomp = False
  testonly = False
  ifn = ''
  ofn = ''
  for opt, arg in opts:
    if opt == '-h':
      usage()
      sys.exit()
    elif opt in ("-i", "--ifile"):
      ifn = arg
    elif opt in ("-o", "--ofile"):
      ofn = arg
    elif opt in ("-d","--decomp"):
      decomp = True
  #---------------
  if os.path.isfile(ifn)==False:
    print("Error: Input file does not exist: " + ifn)
    sys.exit(2)
  if not ofn:
    testonly = True
  indat = readFile(ifn)
  #---------------
  print "Input filesize  : "+str(len(indat))
  if decomp:
    print "Decompressing... "
    outdat = decompress(indat)
    if not outdat:
      print "Error: Decompression failed."
      sys.exit(2)
    if ofn:
      writeFile(ofn,str(bytearray(outdat)))
    else:
      print "Decompress test finished."
  else:
    print "Compressing file "
    outdat = str(bytearray(compress(indat)))
    print "Output filesize : "+str(len(outdat))
    if ofn:
      writeFile(ofn,str(bytearray(outdat)))
    else:
      print "Verifying compression..."
      testdat = decompress(outdat)
      if not testdat:
        print "Test return size: Undefined"
      else:
        print "Test return size: "+str(len(testdat))
        if testdat == indat:
          print "Data set match. Success."
        else:
          print "Data set mismatch. Failure."

  
      
      
      
      

      
      
      
      
      
      




















