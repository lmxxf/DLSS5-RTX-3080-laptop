from pathlib import Path
import sys,json
p=Path(__file__).resolve().parent;r=p.parent;sys.path.insert(0,str(r/'hip'));from phase18_transform import transform
c32=(r/'phase17/artifacts/selected/modules/c32-wave1-fast.generated.cu').read_text();w2=(r/'phase14/artifacts/selected/modules/c64-wave2-fast.generated.cu').read_text()
for site in ['contract','result','v','av','byteout']:transform(w2,[site]);print('PASS',site)
for site in ['c32-prefix','c32-v']:transform(c32,[site]);print('PASS',site)
