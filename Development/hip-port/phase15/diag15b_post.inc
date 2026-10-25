  if(std::getenv("DLSS5_DIAG15B_ARMED")&&std::getenv("DLSS5_DIAG15B_POST"))if(const char*dir=std::getenv("DLSS5_DIAG15B_TRACE")){
   if constexpr(sizeof...(A)==14){if(module=="c32_wave1"&&kernel=="c32_wave1_post_b8"){
    static bool done=false;if(!done){done=true;Synchronize();void*features{};void*scratch{};size_t pixels=size_t(W)*H;api.Check(api.hipMalloc(&features,pixels*64),"15B feature scratch");api.Check(api.hipMalloc(&scratch,pixels*12),"15B RGB scratch");api.Check(api.hipMemsetAsync(features,255,pixels*64,stream),"15B feature poison");
    void*params[15];for(unsigned i=0;i<14;i++)params[i]=argv[i];params[7]=&scratch;params[14]=&features;
    Handle tap=Fn(module,"c32_wave1_post_b8_features");unsigned gg=unsigned(groups?groups:(count+255ull)/256);api.Check(api.hipModuleLaunchKernel(tap,gg,1,1,threads,1,1,0,stream,params,nullptr),"15B independent feature replay");Synchronize();
    auto save=[&](const char*name,void*ptr,size_t bytes){std::vector<char>b(bytes);api.Check(api.hipMemcpy(b.data(),ptr,bytes,2),"15B post read");std::ofstream f(std::string(dir)+"/"+name+".bin",std::ios::binary);f.write(b.data(),bytes);};
    void*color{};void*head{};void*original{};std::memcpy(&color,argv[5],sizeof(color));std::memcpy(&head,argv[6],sizeof(head));std::memcpy(&original,argv[7],sizeof(original));save("post-features",features,pixels*64);save("post-color",color,pixels*16);save("post-head-weights",head,96*4);void*low{};void*skip{};void*scales{};std::memcpy(&low,argv[0],sizeof(low));std::memcpy(&skip,argv[1],sizeof(skip));std::memcpy(&scales,argv[2],sizeof(scales));save("post-low",low,pixels*8);save("post-skip",skip,pixels*32);save("post-scales",scales,64*4);save("post-replay-rgb",scratch,pixels*12);
    std::vector<unsigned>a(pixels*3),b(pixels*3);api.Check(api.hipMemcpy(a.data(),original,pixels*12,2),"15B post original");api.Check(api.hipMemcpy(b.data(),scratch,pixels*12,2),"15B post replay");size_t diff=0;for(size_t i=0;i<a.size();i++)diff+=a[i]!=b[i];float scale{};std::memcpy(&scale,argv[13],4);std::fprintf(stderr,"15B_POST_REPLAY bitdiff=%zu scale=%.9g\n",diff,scale);if(const char*from=std::getenv("DLSS5_DIAG15B_NATIVE_POST_DIR")){
     auto upload=[&](const char*name,size_t bytes){std::vector<char>b(bytes);std::ifstream f(std::string(from)+"/"+name+".bin",std::ios::binary|std::ios::ate);if(!f||size_t(f.tellg())!=bytes)throw std::runtime_error("15B cross replay source size");f.seekg(0);f.read(b.data(),bytes);void*ptr{};api.Check(api.hipMalloc(&ptr,bytes),"15B cross allocate");api.Check(api.hipMemcpy(ptr,b.data(),bytes,1),"15B copied input upload");return ptr;};
     void*clow=upload("post-low",pixels*8),*cskip=upload("post-skip",pixels*32);params[0]=&clow;params[1]=&cskip;
     api.Check(api.hipModuleLaunchKernel(tap,gg,1,1,threads,1,1,0,stream,params,nullptr),"15B isolated F32 on Native inputs");Synchronize();save("post-cross-rgb",scratch,pixels*12);save("post-cross-features",features,pixels*64);
     params[1]=argv[1];api.Check(api.hipModuleLaunchKernel(tap,gg,1,1,threads,1,1,0,stream,params,nullptr),"15B F32 Native-low only");Synchronize();save("post-lowonly-rgb",scratch,pixels*12);
     params[0]=argv[0];params[1]=&cskip;api.Check(api.hipModuleLaunchKernel(tap,gg,1,1,threads,1,1,0,stream,params,nullptr),"15B F32 Native-skip only");Synchronize();save("post-skiponly-rgb",scratch,pixels*12);
     api.hipFree(clow);api.hipFree(cskip);
    }
    api.hipFree(features);api.hipFree(scratch);
   }}}
  }
