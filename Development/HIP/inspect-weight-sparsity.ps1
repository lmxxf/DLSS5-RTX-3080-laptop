$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;
using System.IO;
public static class MatrixSparsity {
 public static string Inspect(string path,string name,int offset,int rows,int columns){
  byte[] bytes=File.ReadAllBytes(path);int total=checked(rows*columns);if(columns%4!=0 || offset<0 || ((long)offset+total)*4>bytes.Length)throw new Exception("matrix range");
  float[] a=new float[total];Buffer.BlockCopy(bytes,offset*4,a,0,total*4);long zeros=0,nonfinite=0,compatible=0,zeroRows=0,outsideGroup=0;
  for(int row=0;row<rows;row++){bool allzero=true;for(int k=0;k<columns;k+=4){int nz=0;for(int j=0;j<4;j++){float v=a[row*columns+k+j];if(v==0)zeros++;else{nz++;allzero=false;if(columns==4*rows && (k+j)/128!=row/32)outsideGroup++;}if(float.IsNaN(v)||float.IsInfinity(v))nonfinite++;}if(nz<=2)compatible++;}if(allzero)zeroRows++;}
  return String.Format(System.Globalization.CultureInfo.InvariantCulture,"{0},{1},{2},{3},{4},{5},{6},{7}",name,rows,columns,zeros,total,compatible,total/4,zeroRows)+","+nonfinite+","+(columns==4*rows?outsideGroup:-1);
 }
}
'@
$a='D:\DLSSNR-Lab\network-720p\DLSS5-AMD\native-game-tiled-assets'
Write-Output 'matrix,rows,columns,zeros,elements,k4_at_most_two_nonzero,k4_groups,zero_rows,nonfinite,nonzero_outside_group128'
foreach($b in 5..65){
 if($b -ge 23 -and $b -le 47){continue}
 $c=if($b -le 8 -or $b -ge 62){64}elseif($b -le 14 -or ($b -ge 56 -and $b -le 61)){128}else{256}
 $cc=$c*$c
 foreach($m in @(@('expand',0,(4*$c),$c),@('contract',(4*$cc),$c,(4*$c)),@('project',(8*$cc),$c,$c))){[MatrixSparsity]::Inspect("$a\block$b-ffn.f32","block$b-ffn-$($m[0])",$m[1],$m[2],$m[3])}
 [MatrixSparsity]::Inspect("$a\block$b-attention.f32","block$b-qkv",0,3*$c,$c)
 [MatrixSparsity]::Inspect("$a\block$b-attention.f32","block$b-attention-project",3*$cc,$c,$c)
}
foreach($b in @('block0','block1','block2','block3','block4','block66','block67','block68','block69','post70')){
 [MatrixSparsity]::Inspect("$a\$b-ffn.f32","$b-ffn-expand",512,128,32)
 [MatrixSparsity]::Inspect("$a\$b-ffn.f32","$b-ffn-contract",4608,32,128)
}
