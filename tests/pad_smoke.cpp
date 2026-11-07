#include "firmware/audio/PadVoice.hpp"
#include <cmath>
#include <cstdio>
#include <vector>
int main(){
 using groovescape::PadVoice;
 PadVoice pad;pad.setEnvironment(1);pad.setIntensity(.65f);pad.noteOn(110.f);
 constexpr unsigned block=128,seconds=3;
 std::vector<float> left(block),right(block);
 double sum=0,peak=0;unsigned count=0;
 for(unsigned i=0;i<PadVoice::kSampleRate*seconds/block;i++){
  std::fill(left.begin(),left.end(),0.f);std::fill(right.begin(),right.end(),0.f);
  pad.render(left.data(),right.data(),block);
  for(unsigned n=0;n<block;n++){if(!std::isfinite(left[n])||!std::isfinite(right[n]))return 2;sum+=left[n]*left[n]+right[n]*right[n];peak=std::max(peak,static_cast<double>(std::max(std::abs(left[n]),std::abs(right[n]))));count+=2;}
 }
 const double rms=std::sqrt(sum/count);
 std::printf("pad smoke test: RMS %.6f peak %.6f\n",rms,peak);
 return rms>0.0001&&peak<1.0?0:1;
}
