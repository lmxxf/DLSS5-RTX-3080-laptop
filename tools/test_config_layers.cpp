// Tests for src/native_config_layers.h (the shared three-layer config reader).
// Linux:   g++ -std=c++17 -I src tools/test_config_layers.cpp -o /tmp/tcl && /tmp/tcl
// Windows: x86_64-w64-mingw32-g++ -std=c++17 -static -I src tools/test_config_layers.cpp -o tcl.exe   (paths become wide)
#include "native_config_layers.h"
#include <cstdio>
#include <cstdlib>
#include <string>
#include <sys/stat.h>
#ifdef _WIN32
#include <direct.h>
static std::wstring W(const std::string&s){return std::wstring(s.begin(),s.end());}
static void setenv_(const char*k,const char*v){_putenv((std::string(k)+"="+v).c_str());}
static void unsetenv_(const char*k){_putenv((std::string(k)+"=").c_str());}
#else
static std::string W(const std::string&s){return s;}
static void setenv_(const char*k,const char*v){setenv(k,v,1);}
static void unsetenv_(const char*k){unsetenv(k);}
#endif
static int failures=0,checks=0;
static std::string dir;
static void put(const char*name,const std::string&text){FILE*f=std::fopen((dir+"/"+name).c_str(),"wb");std::fwrite(text.data(),1,text.size(),f);std::fclose(f);}
static void del(const char*name){std::remove((dir+"/"+name).c_str());}
static void clear(){del("default-config.txt");del("custom-config.txt");del("native-game-flags.txt");}
static std::string get(const NativeConfig&c,const char*k){const auto*e=NativeConfigFind(c,k);return e?"="+e->value:"<absent>";}
static void expect(const char*what,const std::string&got,const std::string&want){
 ++checks;if(got!=want){++failures;std::printf("FAIL %s: got '%s' want '%s'\n",what,got.c_str(),want.c_str());}else std::printf("ok   %s\n",what);}
/* effective config with the environment as it is now (the product takes a snapshot once; tests need it fresh) */
static NativeConfig eff(unsigned*layers=nullptr){NativeConfig c=NativeConfigLoadDir(W(dir),layers);NativeConfigOverlay(c,NativeConfigEnvironmentNow());return c;}

int main(){
 char tmpl[]="/tmp/dlss5-config-layers-XXXXXX";
#ifdef _WIN32
 dir="cfg-test";_mkdir(dir.c_str());
#else
 dir=mkdtemp(tmpl);
#endif
 for(const char*k:{"DLSS5_MULTI_PASS","DLSS5_SKIP_BLOCKS","DLSS5_STYLE","DLSS5_NOTICE","DLSS5_A"})unsetenv_(k);
 unsigned layers=0;

 // 1. only default
 clear();put("default-config.txt","# comment\nDLSS5_MULTI_PASS=1\nDLSS5_STYLE=1\n");
 auto c=eff(&layers);expect("only default: MULTI_PASS",get(c,"DLSS5_MULTI_PASS"),"=1");expect("only default: layers bit",std::to_string(layers),"1");
 expect("only default: NativeConfigDirHasAny",NativeConfigDirHasAny(W(dir))?"yes":"no","yes");

 // 2. custom overrides default; key only in default is kept
 put("custom-config.txt","DLSS5_MULTI_PASS=2\n");
 c=eff(&layers);expect("custom > default",get(c,"DLSS5_MULTI_PASS"),"=2");expect("default kept where custom silent",get(c,"DLSS5_STYLE"),"=1");expect("layers D+C",std::to_string(layers),"3");

 // 3. native overrides custom
 put("native-game-flags.txt","DLSS5_MULTI_PASS=1\r\n");
 c=eff(&layers);expect("native > custom (CRLF file)",get(c,"DLSS5_MULTI_PASS"),"=1");expect("layers D+C+N",std::to_string(layers),"7");

 // 4. environment overrides all three
 setenv_("DLSS5_MULTI_PASS","3");c=eff();expect("env > native > custom > default",get(c,"DLSS5_MULTI_PASS"),"=3");
 setenv_("DLSS5_NOTICE","0");c=eff();expect("env-only key appears",get(c,"DLSS5_NOTICE"),"=0");
 unsetenv_("DLSS5_MULTI_PASS");unsetenv_("DLSS5_NOTICE");

 // 5. missing layers are skipped
 del("custom-config.txt");c=eff(&layers);expect("custom missing: native still wins",get(c,"DLSS5_MULTI_PASS"),"=1");expect("layers D+N",std::to_string(layers),"5");
 del("native-game-flags.txt");put("custom-config.txt","DLSS5_MULTI_PASS=2\n");del("default-config.txt");
 c=eff(&layers);expect("default missing: custom alone",get(c,"DLSS5_MULTI_PASS"),"=2");expect("default missing: STYLE absent",get(c,"DLSS5_STYLE"),"<absent>");
 clear();c=eff(&layers);expect("no file at all: empty",std::to_string(c.size())+"/"+std::to_string(layers),"0/0");
 expect("no file: NativeConfigDirHasAny",NativeConfigDirHasAny(W(dir))?"yes":"no","no");
 put("native-game-flags.txt","DLSS5_STYLE=0\n");c=eff();expect("old user (native only) unchanged",get(c,"DLSS5_STYLE"),"=0");

 // 6. same key twice in one file: last line wins; position = first appearance
 clear();put("custom-config.txt","DLSS5_MULTI_PASS=2\nDLSS5_STYLE=1\nDLSS5_MULTI_PASS=3\n");
 c=eff();expect("duplicate in one file: last wins",get(c,"DLSS5_MULTI_PASS"),"=3");expect("one entry per key",std::to_string(c.size()),"2");

 // 7. empty value overrides the lower layer with empty
 clear();put("default-config.txt","DLSS5_SKIP_BLOCKS=42,43,46\n");put("custom-config.txt","DLSS5_SKIP_BLOCKS=\n");
 c=eff();expect("empty value overrides lower layer",get(c,"DLSS5_SKIP_BLOCKS"),"=");
 put("native-game-flags.txt","DLSS5_SKIP_BLOCKS=42\n");c=eff();expect("native non-empty over custom empty",get(c,"DLSS5_SKIP_BLOCKS"),"=42");

 // 8. line rules (unchanged from the old reader)
 clear();put("default-config.txt","\xEF\xBB\xBF""DLSS5_A=1\n# DLSS5_STYLE=9\n DLSS5_NOTICE=1\nDLSS5_X\nDLSS5_MULTI_PASS=2   \n# 中：注释\nDLSS5_FRAME_STATS=5,a b");
 c=eff();expect("BOM skipped",get(c,"DLSS5_A"),"=1");expect("comment ignored",get(c,"DLSS5_STYLE"),"<absent>");expect("leading space ignored",get(c,"DLSS5_NOTICE"),"<absent>");
 expect("trailing spaces cut",get(c,"DLSS5_MULTI_PASS"),"=2");expect("last line without newline",get(c,"DLSS5_FRAME_STATS"),"=5,a b");
 std::string long_line="DLSS5_HIP_DUP_PREFIX="+std::string(600,'x');put("custom-config.txt",long_line+"\n");c=eff();
 expect("600-byte value not truncated",std::to_string(get(c,"DLSS5_HIP_DUP_PREFIX").size()),"601");
 expect("lines render",NativeConfigLines(NativeConfigParseText("DLSS5_A=1\nDLSS5_B=\n"))[1],"DLSS5_B=");

 clear();std::remove(dir.c_str());
 std::printf("%d/%d checks passed\n",checks-failures,checks);return failures?1:0;
}
