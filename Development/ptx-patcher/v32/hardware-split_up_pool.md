# split_up_pool: four hardware tables

Static counts cover exactly 38 launched FP8 entries. Loop observations below are inherited V2.5 semantic-loop instrumentation, not newly measured hardware-issued counts. Grid/block from V2.3 real NVAPI launches (dynamic shared=0). Occupancy is freshly queried from each actual cubin. No NCU counters are available in this experiment.

## 1. Instructions and loop evidence

|Kernel|nonNOP|HMMA|PRMT|SHF|LOP3|Historical compute loop visits/warp (720p)|
|---|---:|---:|---:|---:|---:|---|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|3942|520|364|27|351|2.0|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|3885|512|372|20|355|unrolled / no compute loop|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|4918|528|429|27|433|unrolled / no compute loop|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|3964|512|364|9|412|unrolled / no compute loop|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|4855|580|364|44|360|unrolled / no compute loop|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|4674|528|316|61|328|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|6271|552|988|55|901|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|5552|608|788|27|744|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|6542|624|859|32|843|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|5412|608|780|11|727|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|6665|552|1083|53|998|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|5761|544|915|26|850|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|7042|576|1036|37|998|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|5733|544|907|16|867|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|6724|584|1105|78|1025|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|5819|576|938|37|862|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|6901|592|1009|67|980|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|5797|576|929|38|872|unrolled / no compute loop|
|cc_split_swin_16h_final_head_512_wait_fp8|1139|64|158|22|156|8.0|
|cc_split_swin_16h_proj_pool_512_chained_fp8|6112|256|489|60|668|7.0|
|cc_split_swin_16h_proj_512_outview_wait_fp8|2883|128|358|72|374|8.0|
|cc_split_swin_16h_proj_512_chained_fp8|1546|64|214|35|210|8.0|
|cc_split_swin_16h_qkv_512_chained_fp8|4515|512|452|58|425|7.0|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|2696|128|342|38|364|8.0|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|2409|128|358|38|342|8.0|
|cc_split_swin_16h_ffwd_512_chained_fp8|1951|192|309|11|306|7.0,8.0|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|3209|384|416|75|505|7.0,8.0|
|cc_vit_1d_projection_chained_fp8|2418|128|344|34|316|7.0|
|cc_vit_1d_projection_wait_fp8|2399|128|344|34|316|7.0|
|cc_vit_1d_attention_chained_fp8|3032|128|368|125|426|5.0|
|cc_vit_1d_qkv_chained_fp8|2782|192|328|20|285|15.0|
|cc_vit_1d_ffn_contract_chained_fp8|3340|256|492|34|453|15.0|
|cc_vit_1d_ffn_expand_chained_fp8|2576|128|287|17|234|16.0|
|cc_vit_1d_ffn_expand_publish_fp8|2472|128|287|13|233|16.0|
|cc_vit_1d_repack_1d_to_2d_fp8|146|0|24|17|16|unrolled / no compute loop|
|cc_vit_1d_repack_2d_to_1d_fp8|208|0|38|26|26|unrolled / no compute loop|
|cc_cb_clear|13|0|0|0|0|unrolled / no compute loop|
|cc_dec_input_upsample_1024_512_tilesync_fp8|3995|128|708|42|646|unrolled / no compute loop|

## 2. Registers and local memory

|Kernel|REG|STACK B|LOCAL B|STL|LDL|
|---|---:|---:|---:|---:|---:|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|205|0|0|0|0|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|168|16|0|4|4|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|168|8|0|1|1|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|168|8|0|2|2|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|242|0|0|0|0|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|168|72|0|15|18|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|168|112|0|24|24|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|168|64|0|11|16|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|168|64|0|11|16|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|166|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|164|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|164|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|203|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|190|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|196|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|198|0|0|0|0|
|cc_split_swin_16h_final_head_512_wait_fp8|136|0|0|0|0|
|cc_split_swin_16h_proj_pool_512_chained_fp8|162|0|0|0|0|
|cc_split_swin_16h_proj_512_outview_wait_fp8|168|0|0|0|0|
|cc_split_swin_16h_proj_512_chained_fp8|141|0|0|0|0|
|cc_split_swin_16h_qkv_512_chained_fp8|255|88|0|40|29|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|166|0|0|0|0|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|167|0|0|0|0|
|cc_split_swin_16h_ffwd_512_chained_fp8|174|0|0|0|0|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|212|0|0|0|0|
|cc_vit_1d_projection_chained_fp8|143|0|0|0|0|
|cc_vit_1d_projection_wait_fp8|143|0|0|0|0|
|cc_vit_1d_attention_chained_fp8|255|0|0|0|0|
|cc_vit_1d_qkv_chained_fp8|199|0|0|0|0|
|cc_vit_1d_ffn_contract_chained_fp8|179|0|0|0|0|
|cc_vit_1d_ffn_expand_chained_fp8|180|0|0|0|0|
|cc_vit_1d_ffn_expand_publish_fp8|172|0|0|0|0|
|cc_vit_1d_repack_1d_to_2d_fp8|19|0|0|0|0|
|cc_vit_1d_repack_2d_to_1d_fp8|20|0|0|0|0|
|cc_cb_clear|8|0|0|0|0|
|cc_dec_input_upsample_1024_512_tilesync_fp8|202|0|0|0|0|

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
|cc_split_swin_16h_proj_pool_512_chained_fp8|128|3|12|[12, 3, 1]|1|[16, 5, 1]|1|
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

Distances count lexical PTX statements from cp.async to next arrive/test_wait, and can cross control flow. They are NOT CFG shortest paths, runtime overlaps, stall counters, or a latency budget. Async completion rewrite is unchanged from the independently audited V2.2 mbarrier path.

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
|cc_split_swin_16h_final_head_512_wait_fp8|0|4|(1, 65)|
|cc_split_swin_16h_proj_pool_512_chained_fp8|256|4|(1, 74)|
|cc_split_swin_16h_proj_512_outview_wait_fp8|0|8|(1, 125)|
|cc_split_swin_16h_proj_512_chained_fp8|0|4|(1, 118)|
|cc_split_swin_16h_qkv_512_chained_fp8|48|4|(1, 1016)|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|0|8|(1, 91)|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|0|8|(1, 122)|
|cc_split_swin_16h_ffwd_512_chained_fp8|0|2|(1, 541)|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|0|16|(1, 1033)|
|cc_vit_1d_projection_chained_fp8|0|4|(1, 61)|
|cc_vit_1d_projection_wait_fp8|0|4|(1, 61)|
|cc_vit_1d_attention_chained_fp8|16|4|(1, 68)|
|cc_vit_1d_qkv_chained_fp8|32|4|(1, 79)|
|cc_vit_1d_ffn_contract_chained_fp8|0|16|(1, 70)|
|cc_vit_1d_ffn_expand_chained_fp8|0|32|(1, 100)|
|cc_vit_1d_ffn_expand_publish_fp8|0|32|(1, 76)|
|cc_vit_1d_repack_1d_to_2d_fp8|0|0|none|
|cc_vit_1d_repack_2d_to_1d_fp8|0|0|none|
|cc_cb_clear|0|0|none|
|cc_dec_input_upsample_1024_512_tilesync_fp8|128|2|(1, 106)|
