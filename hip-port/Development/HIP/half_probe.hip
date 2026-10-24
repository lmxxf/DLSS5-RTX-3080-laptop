// Append to c32_reference.hip. Distinguish language conversions from explicit ISA.
KERNEL void half_probe(const float*input,uint*output,uint count){uint i=lane();if(i>=count)return;float x=input[i];uint packed;
 asm("v_cvt_f16_f32 %0, %1" : "=v"(packed) : "v"(x));
 output[i*4]=bits(H(x));output[i*4+1]=bits(float(_Float16(x)));
 output[i*4+2]=bits(from_half(__builtin_bit_cast(unsigned short,_Float16(x))));
 output[i*4+3]=bits(from_half(packed&65535u));}
