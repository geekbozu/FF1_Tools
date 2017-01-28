Some files I have been working on for translating Final Fantasy 1 for the 3ds

#File List:
##PCK file Spec.txt
Goes over file spec for pck/dpk files

##PCKPAK.py
PCK packer, Currently does not making working PCK's crashes my 3ds when
build it as a cia or use NTR/LayeredFS. With Hans..it just does somethign
funky game doesnt crash but fails to load assets?

##PCKUNPACK.py
Unpacks PCK files, Requires WP16.exe to decompress files

##wp16.c WP16.exe
decompressor used by this version of ff1 as well as the psp version, Written by FireFly over at zenhax



###Extra info
Most of this information has been gleamed from this thread over at zenhax
http://zenhax.com/viewtopic.php?f=9&t=2165&sid=d08c3c0149863fdfab87d25b2c42bc09
eientei95's and firefly's code for the psp port of this really helped this get started.
They really did most of the work that has been done so far. I just re-implemented in python for ease of development. 



#USE

pckunpack.py FILETOUNPACK "FOLDER\TO\UNPACK\TO"

Decompression has been tested most visual assets are compressed and have been
succsessfully been able to extract images. 

Packing of DPK/PCK files still needs work. There is a 0x2 byte field in the file structure that I do not know what is nor have I put the time in with a debugger to figure out. Currently the depacker prepends it to the file name. 

