/* Render a short offline ToneScape preview without touching FM1 hardware. */
#include "../firmware/audio/pad_dsp.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
static void w16(FILE *f,uint16_t x){fputc(x&255,f);fputc(x>>8,f);}
static void w32(FILE *f,uint32_t x){w16(f,(uint16_t)x);w16(f,(uint16_t)(x>>16));}
int main(int argc,char **argv){
 if(argc!=2){fprintf(stderr,"usage: preview OUTPUT.wav\n");return 2;}
 FILE *f=fopen(argv[1],"wb");if(!f){perror(argv[1]);return 2;}
 const uint32_t frames=44100u*6u,bytes=frames*4u;
 fwrite("RIFF",1,4,f);w32(f,36u+bytes);fwrite("WAVEfmt ",1,8,f);
 w32(f,16);w16(f,1);w16(f,2);w32(f,44100);w32(f,176400);
 w16(f,4);w16(f,16);fwrite("data",1,4,f);w32(f,bytes);
 static gs_pad p;int32_t lr[512];gs_pad_init(&p);
 gs_pad_environment(&p,5,0.75f);gs_pad_note(&p,110.0f,1);
 for(uint32_t start=0;start<frames;start+=256u){
  uint32_t count=frames-start;if(count>256u)count=256u;
  if(start>=44100u*4u && p.gate)gs_pad_note(&p,0.0f,0);
  gs_pad_render(&p,lr,count,4096);
  for(uint32_t i=0;i<count*2u;i++){
   int32_t x=lr[i]/256;
   if(x>32767)x=32767;
   if(x< -32768)x= -32768;
   w16(f,(uint16_t)(int16_t)x);
  }
 }
 if(fclose(f)!=0)return 3;
 printf("Rendered %u frames of 44.1kHz stereo preview\n",frames);
 return 0;
}
