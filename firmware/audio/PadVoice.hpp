#pragma once
#include <array>
#include <cmath>
#include <cstdint>
#include <algorithm>
namespace groovescape {
// Portable, allocation-free ToneScape-inspired stereo pad core.
// Host and FM1 can call render() at the same sample rate.
// Original implementation based on the user's ToneScape V2 environment parameters.
class PadVoice {
public:
 static constexpr unsigned kSampleRate=48000;
 struct Environment {const char* name;float body,brightness,inharmonic,breath,space;};
 static constexpr std::array<Environment,16> environments{{
 {"Drift",.72f,.25f,.08f,.62f,.55f},{"Bloom",.82f,.33f,.06f,.40f,.64f},
 {"Ember",.62f,.45f,.16f,.25f,.42f},{"Glass Choir",.54f,.68f,.22f,.36f,.78f},
 {"Deep Forest",.76f,.20f,.18f,.72f,.48f},{"Cathedral",.88f,.52f,.11f,.30f,.92f},
 {"Ocean",.80f,.28f,.13f,.86f,.72f},{"Rift",.64f,.74f,.38f,.34f,.74f},
 {"Mist",.50f,.30f,.10f,.92f,.82f},{"Machine Air",.58f,.48f,.42f,.28f,.56f},
 {"Tape Ghost",.74f,.24f,.09f,.46f,.58f},{"Hollow Earth",.90f,.26f,.30f,.44f,.66f},
 {"Neon Weather",.56f,.72f,.24f,.58f,.76f},{"Ice Bloom",.48f,.82f,.20f,.32f,.88f},
 {"Aurora Body",.70f,.56f,.15f,.68f,.84f},{"Noir Void",.84f,.18f,.36f,.52f,.90f}
 }};
 void noteOn(float hz){frequency_=std::clamp(hz,30.f,1500.f);target_=1.f;}
 void noteOff(){target_=0.f;}
 void setEnvironment(unsigned index){environment_=index%environments.size();}
 void setIntensity(float value){intensity_=std::clamp(value,0.f,1.f);}
 void render(float* left,float* right,unsigned frames){
  const auto& e=environments[environment_];
  constexpr float pi2=6.283185307179586f;
  for(unsigned n=0;n<frames;n++){
   const float rate=target_>envelope_?1.f/(kSampleRate*2.5f):1.f/(kSampleRate*5.f);
   envelope_+= (target_-envelope_)*rate;
   phase_+=pi2*frequency_/kSampleRate;
   if(phase_>=pi2)phase_-=pi2;
   driftPhase_+=pi2*.11f/kSampleRate;
   if(driftPhase_>=pi2)driftPhase_-=pi2;
   const float drift=.003f*std::sin(driftPhase_)*(.4f+intensity_);
   float l=0,r=0,total=0;
   const unsigned partialCount=4+static_cast<unsigned>(intensity_*8);
   for(unsigned p=0;p<partialCount;p++){
    const float harmonic=static_cast<float>(p+1);
    const float stretch=1.f+e.inharmonic*.006f*static_cast<float>(static_cast<int>(p%3)-1);
    const float weight=1.f/std::pow(harmonic,.85f+e.brightness*.5f);
    const float angle=phase_*harmonic*stretch*(1.f+drift*(1.f+p*.06f));
    const float spread=.2f+e.space*.7f;
    l+=std::sin(angle+p*.21f)*weight*(1.f+spread*.15f*std::sin(driftPhase_+p));
    r+=std::sin(angle+p*.21f+.06f*p)*weight*(1.f-spread*.15f*std::sin(driftPhase_+p));
    total+=weight;
   }
   const float amplitude=envelope_*e.body*.28f/(total>0.f?total:1.f);
   left[n]+=std::tanh(l*amplitude);
   right[n]+=std::tanh(r*amplitude);
  }
 }
private:
 unsigned environment_=0;float frequency_=110.f,phase_=0.f,driftPhase_=0.f,envelope_=0.f,target_=0.f,intensity_=.5f;
};
} // namespace groovescape
