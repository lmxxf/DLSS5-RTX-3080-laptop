# Coordinate check against NVIDIA PTX ISA m16n8k32 FP8 / m16n8k16 FP16.
# Labels below refer to scalar elements, unlike the generator's pair-register names.
errors=[]
for lane in range(32):
 g,t=lane//4,lane%4
 for half in range(2):
  # Generated FP16 pair ordering: A [orig0_s0,orig1_s0,orig0_s1,orig1_s1].
  for pair,(reg,which) in enumerate([(2*half,0),(2*half+1,0),(2*half,1),(2*half+1,1)]):
   src_lane=g*4+t//2+2*which
   for elem in range(2):
    i=reg*4+2*(t%2)+elem
    actual=(g+(8 if 4<=i<8 or i>=12 else 0),4*(src_lane%4)+(i%4)+(16 if i>=8 else 0))
    j=pair*2+elem
    expect=(g+(8 if j in [2,3,6,7] else 0),2*t+j%2+(8 if j>=4 else 0)+16*half)
    if actual!=expect:errors.append(('A',lane,half,j,actual,expect))
  for pair in range(2):
   src_lane=g*4+t//2+pair*2
   for elem in range(2):
    i=half*4+2*(t%2)+elem
    actual=(4*(src_lane%4)+i%4+16*half,g)
    expect=(2*t+elem+8*pair+16*half,g)
    if actual!=expect:errors.append(('B',lane,half,pair,actual,expect))
print('Coordinate mismatches:',len(errors),'(A 512 + B 256 scalar slots)')
assert not errors,errors[:3]
