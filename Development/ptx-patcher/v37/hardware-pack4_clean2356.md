# pack4_clean2356: four hardware tables

Static counts cover exactly 38 launched FP8 entries. Loop observations below are inherited V2.5 semantic-loop instrumentation, not newly measured hardware-issued counts. Grid/block from V2.3 real NVAPI launches (dynamic shared=0). Occupancy is freshly queried from each actual cubin. No NCU counters are available in this experiment.

## 1. Instructions and loop evidence

|Kernel|nonNOP|HMMA|PRMT|SHF|LOP3|Historical compute loop visits/warp (720p)|
|---|---:|---:|---:|---:|---:|---|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|3943|520|356|27|379|2.0|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|3889|512|364|20|383|unrolled / no compute loop|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|4899|528|420|27|465|unrolled / no compute loop|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|3993|512|363|9|444|unrolled / no compute loop|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|4876|580|356|44|396|unrolled / no compute loop|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|4674|528|316|61|328|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|6321|552|979|55|997|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|5596|608|780|27|804|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|6581|624|851|32|903|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|5481|608|780|11|791|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|6555|552|1075|53|1094|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|5685|544|907|26|910|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|6924|576|1027|38|1062|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|5676|544|907|22|934|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|6649|584|1097|78|1117|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|5729|576|930|37|922|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|6792|592|1001|67|1040|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|5733|576|929|38|936|unrolled / no compute loop|
|cc_split_swin_16h_final_head_512_wait_fp8|1103|64|150|22|152|8.0|
|cc_split_swin_16h_proj_pool_512_chained_fp8|6001|256|472|63|633|7.0|
|cc_split_swin_16h_proj_512_outview_wait_fp8|2844|128|326|73|422|8.0|
|cc_split_swin_16h_proj_512_chained_fp8|1514|64|198|35|234|8.0|
|cc_split_swin_16h_qkv_512_chained_fp8|4462|512|444|58|421|7.0|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|2682|128|326|37|420|8.0|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|2369|128|326|37|390|8.0|
|cc_split_swin_16h_ffwd_512_chained_fp8|1933|192|305|11|304|7.0,8.0|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|3209|384|416|75|505|7.0,8.0|
|cc_vit_1d_projection_chained_fp8|2332|128|320|34|368|7.0|
|cc_vit_1d_projection_wait_fp8|2331|128|320|34|368|7.0|
|cc_vit_1d_attention_chained_fp8|2936|128|352|127|418|5.0|
|cc_vit_1d_qkv_chained_fp8|2654|192|320|20|281|15.0|
|cc_vit_1d_ffn_contract_chained_fp8|3250|256|460|34|501|15.0|
|cc_vit_1d_ffn_expand_chained_fp8|2368|128|255|17|218|16.0|
|cc_vit_1d_ffn_expand_publish_fp8|2264|128|255|13|217|16.0|
|cc_vit_1d_repack_1d_to_2d_fp8|146|0|24|17|16|unrolled / no compute loop|
|cc_vit_1d_repack_2d_to_1d_fp8|208|0|38|26|26|unrolled / no compute loop|
|cc_cb_clear|13|0|0|0|0|unrolled / no compute loop|
|cc_dec_input_upsample_1024_512_tilesync_fp8|3855|128|672|42|756|unrolled / no compute loop|

## 2. Registers and local memory

|Kernel|REG|STACK B|LOCAL B|STL|LDL|
|---|---:|---:|---:|---:|---:|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|208|0|0|0|0|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|168|16|0|4|4|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|168|8|0|1|1|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|168|8|0|2|2|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|242|0|0|0|0|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|168|80|0|15|19|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|168|104|0|23|23|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|168|64|0|11|15|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|168|64|0|11|15|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|166|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|166|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|164|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|203|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|190|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|196|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|198|0|0|0|0|
|cc_split_swin_16h_final_head_512_wait_fp8|136|0|0|0|0|
|cc_split_swin_16h_proj_pool_512_chained_fp8|180|0|0|0|0|
|cc_split_swin_16h_proj_512_outview_wait_fp8|168|0|0|0|0|
|cc_split_swin_16h_proj_512_chained_fp8|141|0|0|0|0|
|cc_split_swin_16h_qkv_512_chained_fp8|255|88|0|33|22|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|166|0|0|0|0|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|168|0|0|0|0|
|cc_split_swin_16h_ffwd_512_chained_fp8|174|0|0|0|0|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|212|0|0|0|0|
|cc_vit_1d_projection_chained_fp8|148|0|0|0|0|
|cc_vit_1d_projection_wait_fp8|146|0|0|0|0|
|cc_vit_1d_attention_chained_fp8|255|0|0|0|0|
|cc_vit_1d_qkv_chained_fp8|197|0|0|0|0|
|cc_vit_1d_ffn_contract_chained_fp8|179|0|0|0|0|
|cc_vit_1d_ffn_expand_chained_fp8|178|0|0|0|0|
|cc_vit_1d_ffn_expand_publish_fp8|172|0|0|0|0|
|cc_vit_1d_repack_1d_to_2d_fp8|19|0|0|0|0|
|cc_vit_1d_repack_2d_to_1d_fp8|20|0|0|0|0|
|cc_cb_clear|8|0|0|0|0|
|cc_dec_input_upsample_1024_512_tilesync_fp8|203|0|0|0|0|

## 3. Official resident limit and finite grid

Waves = ceil(grid CTAs / (48 SM * theoretical resident CTAs)); this is capacity arithmetic, not measured concurrency. Multiple calls may use different grids; raw launch source remains v23/profile.json.

|Kernel|Threads|CTA/SM|Warps/SM|720 grid|720 capacity waves|1080 grid|1080 capacity waves|
|---|---:|---:|---:|---|---:|---|---:|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|32|8|8|[85, 48, 1]|11|[121, 72, 1]|23|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|32|12|12|[84, 49, 1]|8|[120, 73, 1]|16|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|32|12|12|[85, 49, 1]|8|[121, 73, 1]|16|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|32|12|12|[84, 48, 1]|7|[120, 72, 1]|15|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|32|8|8|[169, 97, 1]|43|[241, 145, 1]|92|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|32|12|12|[168, 96, 1]|28|[240, 144, 1]|60|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|64|6|12|[43, 24, 1]|4|[61, 36, 1]|8|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|64|6|12|[42, 25, 1]|4|[60, 37, 1]|8|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|64|6|12|[43, 25, 1]|4|[61, 37, 1]|8|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|64|6|12|[42, 24, 1]|4|[60, 36, 1]|8|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|128|3|12|[22, 12, 1]|2|[31, 18, 1]|4|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|128|3|12|[21, 13, 1]|2|[30, 19, 1]|4|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|128|3|12|[22, 13, 1]|2|[31, 19, 1]|5|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|128|3|12|[21, 12, 1]|2|[30, 18, 1]|4|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|256|1|8|[11, 6, 1]|2|[16, 9, 1]|3|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|256|1|8|[11, 7, 1]|2|[15, 10, 1]|4|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|256|1|8|[11, 7, 1]|2|[16, 10, 1]|4|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|256|1|8|[11, 6, 1]|2|[15, 9, 1]|3|
|cc_split_swin_16h_final_head_512_wait_fp8|256|1|8|[12, 2, 1]|1|[16, 3, 1]|1|
|cc_split_swin_16h_proj_pool_512_chained_fp8|128|2|8|[12, 3, 1]|1|[16, 5, 1]|1|
|cc_split_swin_16h_proj_512_outview_wait_fp8|128|3|12|[12, 3, 1]|1|[16, 5, 1]|1|
|cc_split_swin_16h_proj_512_chained_fp8|256|1|8|[12, 3, 1]|1|[16, 5, 1]|2|
|cc_split_swin_16h_qkv_512_chained_fp8|128|2|8|[6, 3, 4]|1|[8, 5, 4]|2|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|128|3|12|[12, 3, 1]|1|[16, 5, 1]|1|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|128|3|12|[12, 3, 1]|1|[16, 5, 1]|1|
|cc_split_swin_16h_ffwd_512_chained_fp8|256|1|8|[6, 3, 2]|1|[8, 5, 2]|2|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|128|2|8|[6, 3, 2]|1|[8, 5, 2]|1|
|cc_vit_1d_projection_chained_fp8|128|3|12|[24, 1, 4]|1|[40, 1, 4]|2|
|cc_vit_1d_projection_wait_fp8|128|3|12|[24, 1, 4]|1|[40, 1, 4]|2|
|cc_vit_1d_attention_chained_fp8|128|2|8|[32, 2, 1]|1|[32, 3, 1]|1|
|cc_vit_1d_qkv_chained_fp8|128|2|8|[48, 1, 2]|1|[80, 1, 2]|2|
|cc_vit_1d_ffn_contract_chained_fp8|128|2|8|[24, 1, 4]|1|[40, 1, 4]|2|
|cc_vit_1d_ffn_expand_chained_fp8|128|2|8|[96, 1, 1]|1|[160, 1, 1]|2|
|cc_vit_1d_ffn_expand_publish_fp8|128|2|8|[96, 1, 1]|1|[160, 1, 1]|2|
|cc_vit_1d_repack_1d_to_2d_fp8|256|6|48|[288, 1, 1]|1|[640, 1, 1]|3|
|cc_vit_1d_repack_2d_to_1d_fp8|256|6|48|[288, 1, 1]|1|[640, 1, 1]|3|
|cc_cb_clear|256|6|48|[84, 1, 1]|1|[143, 1, 1]|1|
|cc_dec_input_upsample_1024_512_tilesync_fp8|64|4|8|[12, 3, 4]|1|[16, 5, 4]|2|

## 4. Shuffle and async wait distance

Distances count lexical PTX statements from cp.async to next arrive/test_wait, and can cross control flow. They are NOT CFG shortest paths, runtime overlaps, stall counters, or a latency budget. Original async completion retains the independently audited V2.2 mbarrier path; V3.7 async candidates additionally build and synchronize a decoded half view at certified publication points.

|Kernel|SASS SHFL|SASS LDGSTS|PTX async-to-next-wait lexical distance range|
|---|---:|---:|---|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|80|0|none|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|48|0|none|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|80|0|none|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|48|0|none|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|88|0|none|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|80|0|none|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|80|0|none|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|48|0|none|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|80|0|none|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|48|0|none|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|80|0|none|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|48|0|none|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|80|0|none|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|48|0|none|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|80|0|none|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|48|0|none|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|80|0|none|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|48|0|none|
|cc_split_swin_16h_final_head_512_wait_fp8|0|4|(1, 55)|
|cc_split_swin_16h_proj_pool_512_chained_fp8|256|4|(1, 64)|
|cc_split_swin_16h_proj_512_outview_wait_fp8|0|8|(1, 115)|
|cc_split_swin_16h_proj_512_chained_fp8|0|4|(1, 108)|
|cc_split_swin_16h_qkv_512_chained_fp8|48|4|(1, 1006)|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|0|8|(1, 81)|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|0|8|(1, 112)|
|cc_split_swin_16h_ffwd_512_chained_fp8|0|2|(1, 531)|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|0|16|(1, 1033)|
|cc_vit_1d_projection_chained_fp8|0|4|(1, 51)|
|cc_vit_1d_projection_wait_fp8|0|4|(1, 51)|
|cc_vit_1d_attention_chained_fp8|16|4|(1, 58)|
|cc_vit_1d_qkv_chained_fp8|32|4|(1, 69)|
|cc_vit_1d_ffn_contract_chained_fp8|0|16|(1, 60)|
|cc_vit_1d_ffn_expand_chained_fp8|0|32|(1, 90)|
|cc_vit_1d_ffn_expand_publish_fp8|0|32|(1, 66)|
|cc_vit_1d_repack_1d_to_2d_fp8|0|0|none|
|cc_vit_1d_repack_2d_to_1d_fp8|0|0|none|
|cc_cb_clear|0|0|none|
|cc_dec_input_upsample_1024_512_tilesync_fp8|128|2|(1, 96)|
