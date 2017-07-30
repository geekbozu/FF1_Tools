/* This file is part of FF1DS_PK which is released under the MIT License.
   See LICENSE for full license details.                                    */

#include <stdint.h>
#include "main.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// a sample exported function
void DLL_EXPORT SomeFunction(const LPCSTR sometext)
{
    MessageBoxA(0, sometext, "DLL Message", MB_OK | MB_ICONINFORMATION);
}

#define BACKREF_SIZE 0x800
#define BACKREF_DIST (BACKREF_SIZE-1)
#define MAX_CODE_LEN 33
#define MAX(x, y) (((x) > (y)) ? (x) : (y))
#define MIN(x, y) (((x) < (y)) ? (x) : (y))

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;


/*If count is...
   0: Backref is treated as a literal.
  -1: Backref is ignored. Immediately flush buffer.
  >1: An actual LZ codeword    */
void emit(uint16_t *arr, int *pos, int backref, int ct){
    static uint32_t flags;
    static int flagpos;
    static uint16_t buf[33];
    if (!ct) {
        buf[flagpos] = backref;
        flags |= 1<<flagpos;
        flagpos++;
    }
    else if (ct > 1) {
        buf[flagpos] = (backref<<5) + ct - 2;
        flagpos++;
    }
    else if (ct == 1) {
        //Well fuck. Something went horribly wrong.
        exit(-1);
    }
    if ((flagpos>31) || (ct < 0)) {
        if (flagpos) {
            memcpy(arr+*pos,&flags,sizeof(flags));
            *pos += 2;
            memcpy(arr+*pos,buf,flagpos*sizeof(uint16_t));
        }
        *pos += flagpos;
        flagpos = 0;
        flags = 0;
    }
    return;
}

/* in_buffer_size in words, NOT bytes */
int DLL_EXPORT get_max_compressed_size(int in_buffer_size){
    return in_buffer_size/32*33;
}
/* Returns size (in words) of compressed object. Buffers MUST be large enough to
   store a complete copy. in_buffer_size is in words, NOT bytes.
   Does NOT return Wp16 header information. Must be constructed yourself. */
int DLL_EXPORT compress(uint16_t *in_buffer,int in_buffer_size, uint16_t *out_buffer){
    /* Initializations */
    int i;
    int j;
    int t;
    int found_len;
    int found_ptr;
    int temp_len;
    int temp_ptr;
    int out_buffer_ptr = 0;
    int in_buffer_ptr = 0;
    /* Emit first byte literal to prime the compressor */
    emit(out_buffer,&out_buffer_ptr,in_buffer[0],0);
    in_buffer_ptr++;

    /* Start compression loop. Read from in_buffer, write to out_buffer */
    while (1){
        found_len = -1;
        found_ptr = 0;
        //Begin scanning starting at the back of the window to the in_buffer_ptr
        for(i=MAX(0,in_buffer_ptr-BACKREF_DIST) ; i<in_buffer_ptr ; i++){
            temp_len = 0;
            temp_ptr = in_buffer_ptr;
            t = MIN(i+MAX_CODE_LEN,in_buffer_size-1);
            for(j=i ; j<t ; j++){
                if (in_buffer[j]==in_buffer[temp_ptr]){
                    temp_ptr++;
                    temp_len++;
                    if ((temp_len==MAX_CODE_LEN) ||(temp_ptr>=(in_buffer_size-1))) break;
                }
                else break;
            }
            if ((temp_len>1) && (temp_len>found_len)){
                found_len = temp_len;
                found_ptr = i;
            }
        }
        if (found_len<2){
            //printf("LIT %i\n",in_buffer[in_buffer_ptr]);
            emit(out_buffer,&out_buffer_ptr,in_buffer[in_buffer_ptr],0);
            in_buffer_ptr++;
        }
        else {
            //printf("LZC %i,%i\n",in_buffer_ptr,found_len);
            emit(out_buffer,&out_buffer_ptr,in_buffer_ptr-found_ptr,found_len);
            in_buffer_ptr += found_len;
        }
        if (in_buffer_ptr >= in_buffer_size) {
            emit(out_buffer,&out_buffer_ptr,0,-1);
            break;
        }
    }
    return out_buffer_ptr;
}
/* All sizes are in words, not bytes. When was it ever bytes?
   Offset is distance from SoF to start of data (skip over header)

*/
int DLL_EXPORT get_decomp_size(uint16_t *in_buffer,int in_buffer_size,int offset_to_data){
    int flag_count = 32;
    int output_size = 0; //In words, not bytes
    uint32_t flags;
    while (offset_to_data<in_buffer_size){
        if (flag_count>31){
            flags = in_buffer[offset_to_data+0]+(in_buffer[offset_to_data+1]<<16);
            offset_to_data+=2;
            flag_count = 0;
        }
        if (flags&(1<<flag_count))  output_size++;
        else                        output_size += (in_buffer[offset_to_data]&0x1F)+2;
        flag_count++;
        offset_to_data++;
    }
    return output_size;
}

/* Decompression of Wp16 data stored in array. Contains header */
int DLL_EXPORT decompress(uint16_t *in_buffer, int in_buffer_size, uint16_t *out_buffer, int offset_to_data)
{
    uint16_t history[BACKREF_SIZE];
    memset(history, 0, BACKREF_SIZE*sizeof(uint16_t));
    int in_buffer_ptr = offset_to_data; //Reading location start
    int out_buffer_ptr = 0;             //location to write out to
    int hptr = 0;  //Also writing out to here, our circular buffer (1)
    int i,t,v,d;
    uint32_t flags;
    int flag_count = 32;
    while (in_buffer_ptr<in_buffer_size){
        if (flag_count>31){
            flags = in_buffer[in_buffer_ptr]+(in_buffer[in_buffer_ptr+1]<<16);
            in_buffer_ptr+=2;
            flag_count = 0;
        }
        if (flags&(1<<flag_count)) {
            history[hptr] = in_buffer[in_buffer_ptr];
            out_buffer[out_buffer_ptr] = history[hptr];
            hptr = (hptr+1)&BACKREF_DIST;
            out_buffer_ptr++;
        }
        else {
            t = in_buffer[in_buffer_ptr];
            d = (t>>5)&BACKREF_DIST;
            for(i=0;i<(t&0x1F)+2;i++){
                v = history[(hptr-d)&BACKREF_DIST];
                history[hptr] = v;
                out_buffer[out_buffer_ptr] = v;
                hptr = (hptr+1)&BACKREF_DIST;
                out_buffer_ptr++;
            }
        }
        in_buffer_ptr++;
        flag_count++;
    }
    return 0;
}
/* 1. Yes. We actually need one due to back-references in some files indicating
      a position before the start of the data stream, expecting zeros to be there.
      This is something we don't do in our compressor, tho.
*/

extern "C" DLL_EXPORT BOOL APIENTRY DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved)
{
    switch (fdwReason)
    {
        case DLL_PROCESS_ATTACH:
            // attach to process
            // return FALSE to fail DLL load
            break;

        case DLL_PROCESS_DETACH:
            // detach from process
            break;

        case DLL_THREAD_ATTACH:
            // attach to thread
            break;

        case DLL_THREAD_DETACH:
            // detach from thread
            break;
    }
    return TRUE; // succesful
}
