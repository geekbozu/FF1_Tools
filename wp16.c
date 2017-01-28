 
 
#include <stdint.h>
#include <stdio.h>
#include <string.h>
 
typedef uint8_t  u8;
typedef uint16_t u16;
typedef uint32_t u32;
 
void decompress(FILE *in, FILE *out, size_t compressed_size) {
  #define CONTEXT 0x800
  #define BIT(n, b) (((n) >> (b)) & 1)
 
  u16 history[CONTEXT];
  memset(history, 0, sizeof(u16) * CONTEXT);
  size_t i = 0, written = 0;
  size_t start = ftell(in);
 
  #define WRITE(x) {                          \
    history[i] = (x);                         \
    fwrite(&history[i], sizeof(u16), 1, out); \
    written++;                                \
    i = (i + 1) & (CONTEXT - 1);              \
  }
  #define HISTORY(delta) history[(i - (delta)) & (CONTEXT - 1)]
 
  while (!feof(in) && ftell(in) < start + compressed_size) {
    u8 flags[4];
    fread(&flags, sizeof(u8), 4, in);
 
    u16 vs[32];
    fread(vs, sizeof(u16), 32, in);
 
    for (size_t b = 0; b < 32; b++) {
      if (BIT(flags[b >> 3], b & 0x7)) { // Copy verbatim
        WRITE(vs[b]);
 
      } else { // Copy from history
        size_t count = (vs[b] & 0x1F) + 2,
               dist  = (vs[b] >> 5);
        for (size_t k = 0; k < count; k++) WRITE(HISTORY(dist))
       }
    }
  }
 
  #undef CONTEXT
  #undef BIT
  #undef WRITE
  #undef HISTORY
}
 
int main(int argc, char *argv[]) {
  if (argc != 3) {
    fprintf(stderr, "Usage: %s <in_filename> <out_filename>\n", argv[1]);
    return 1;
  }
 
  FILE *fi = fopen(argv[1], "rb");
  if (fi == NULL) {
    fprintf(stderr, "Couldn't open '%s' for reading.\n", argv[1]);
    return 1;
  }
 
  // Header
  char magic[4];
  fread(magic, sizeof(char), 4, fi);
  if (strncmp(magic, "Wp16", 4) != 0)
  {
    fprintf(stderr, "Magic value '%s' does not match \"Wp16\"\n", magic);
    fclose(fi);
    return 1;
  }
  u32 filesize;
  fread(&filesize, sizeof(u32), 1, fi);
 
 
  FILE *fo = fopen(argv[2], "wb");
  if (fo == NULL) {
    fprintf(stderr, "Couldn't open '%s' for writing.\n", argv[2]);
    fclose(fi);
    return 1;
  }
  // Compressed data
  decompress(fi, fo, filesize - 8);
  return 0;
}
