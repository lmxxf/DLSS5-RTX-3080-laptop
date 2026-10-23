#pragma once
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <atomic>
// Product mode and number of network evaluations are separate: Small 0.5x runs once.
namespace dlss5_mode {
inline unsigned Parse(const char*v){if(!v||!*v||!std::strcmp(v,"0.5"))return 0;
 for(unsigned n=1;n<=3;n++)if(v[0]==char('0'+n)&&!v[1])return n;
 std::fprintf(stderr,"DLSS5_MULTI_PASS=%s invalid (0.5/1/2/3), using 0.5\n",v);return 0;}
inline unsigned Environment(){return Parse(std::getenv("DLSS5_MULTI_PASS"));}
inline std::atomic<int> hot_mode{-1};
inline unsigned Requested(){int n=hot_mode.load(std::memory_order_relaxed);return n<0?Environment():unsigned(n);}
inline void Request(unsigned n){if(n<=3)hot_mode.store(int(n),std::memory_order_relaxed);}
inline const char* Name(unsigned mode){static const char*names[]={"0.5","1","2","3"};return names[mode<=3?mode:0];}
inline unsigned Passes(unsigned mode){return mode?mode:1;}
inline unsigned Next(unsigned mode){return mode<3?mode+1:0;}
}
