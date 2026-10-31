# probe_both: four hardware tables

Static counts cover exactly 38 launched FP8 entries. Loop observations below are inherited V2.5 semantic-loop instrumentation, not newly measured hardware-issued counts. Grid/block from V2.3 real NVAPI launches (dynamic shared=0). Occupancy is freshly queried from each actual cubin. No NCU counters are available in this experiment.

## 1. Instructions and loop evidence

|Kernel|nonNOP|HMMA|PRMT|SHF|LOP3|Historical compute loop visits/warp (720p)|
|---|---:|---:|---:|---:|---:|---|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|3076|520|140|27|159|2.0|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|3064|512|163|22|176|unrolled / no compute loop|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|3967|528|189|27|225|unrolled / no compute loop|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|3150|512|155|9|236|unrolled / no compute loop|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|4004|580|139|44|176|unrolled / no compute loop|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|3819|528|108|58|117|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|4294|552|476|58|487|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|3378|608|275|22|288|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|4268|624|299|33|345|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|3366|608|267|13|302|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|4325|552|475|51|486|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|3434|544|323|23|318|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|4348|576|347|36|372|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|3420|544|315|20|340|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|4470|584|513|78|529|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|3573|576|361|37|350|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|4755|816|385|67|420|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|3554|576|353|38|360|unrolled / no compute loop|
|cc_split_swin_16h_final_head_512_wait_fp8|750|64|62|22|60|8.0|
|cc_split_swin_16h_proj_pool_512_chained_fp8|5093|256|232|63|477|7.0|
|cc_split_swin_16h_proj_512_outview_wait_fp8|2463|128|230|73|310|8.0|
|cc_split_swin_16h_proj_512_chained_fp8|1188|64|118|35|146|8.0|
|cc_split_swin_16h_qkv_512_chained_fp8|3266|512|132|61|105|7.0|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|2245|128|214|38|300|8.0|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|1990|128|230|38|278|8.0|
|cc_split_swin_16h_ffwd_512_chained_fp8|946|192|52|12|50|7.0,8.0|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|1958|384|96|76|185|7.0,8.0|
|cc_vit_1d_projection_chained_fp8|1977|128|216|34|252|7.0|
|cc_vit_1d_projection_wait_fp8|1970|128|216|34|252|7.0|
|cc_vit_1d_attention_chained_fp8|2775|128|304|125|362|5.0|
|cc_vit_1d_qkv_chained_fp8|2155|192|168|20|125|15.0|
|cc_vit_1d_ffn_contract_chained_fp8|2431|256|236|34|261|15.0|
|cc_vit_1d_ffn_expand_chained_fp8|2061|128|158|17|106|16.0|
|cc_vit_1d_ffn_expand_publish_fp8|1962|128|158|13|105|16.0|
|cc_vit_1d_repack_1d_to_2d_fp8|146|0|24|17|16|unrolled / no compute loop|
|cc_vit_1d_repack_2d_to_1d_fp8|208|0|38|26|26|unrolled / no compute loop|
|cc_cb_clear|13|0|0|0|0|unrolled / no compute loop|
|cc_dec_input_upsample_1024_512_tilesync_fp8|2955|128|420|42|486|unrolled / no compute loop|

## 2. Registers and local memory

|Kernel|REG|STACK B|LOCAL B|STL|LDL|
|---|---:|---:|---:|---:|---:|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|202|0|0|0|0|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|168|0|0|0|0|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|242|0|0|0|0|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|168|32|0|5|5|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|166|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|166|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|202|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|190|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|195|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|196|0|0|0|0|
|cc_split_swin_16h_final_head_512_wait_fp8|106|0|0|0|0|
|cc_split_swin_16h_proj_pool_512_chained_fp8|162|0|0|0|0|
|cc_split_swin_16h_proj_512_outview_wait_fp8|134|0|0|0|0|
|cc_split_swin_16h_proj_512_chained_fp8|112|0|0|0|0|
|cc_split_swin_16h_qkv_512_chained_fp8|255|88|0|33|22|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|132|0|0|0|0|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|134|0|0|0|0|
|cc_split_swin_16h_ffwd_512_chained_fp8|144|0|0|0|0|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|208|0|0|0|0|
|cc_vit_1d_projection_chained_fp8|138|0|0|0|0|
|cc_vit_1d_projection_wait_fp8|138|0|0|0|0|
|cc_vit_1d_attention_chained_fp8|255|0|0|0|0|
|cc_vit_1d_qkv_chained_fp8|164|0|0|0|0|
|cc_vit_1d_ffn_contract_chained_fp8|155|0|0|0|0|
|cc_vit_1d_ffn_expand_chained_fp8|152|0|0|0|0|
|cc_vit_1d_ffn_expand_publish_fp8|144|0|0|0|0|
|cc_vit_1d_repack_1d_to_2d_fp8|19|0|0|0|0|
|cc_vit_1d_repack_2d_to_1d_fp8|20|0|0|0|0|
|cc_cb_clear|8|0|0|0|0|
|cc_dec_input_upsample_1024_512_tilesync_fp8|219|0|0|0|0|

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
|cc_split_swin_16h_final_head_512_wait_fp8|256|2|16|[12, 2, 1]|1|[16, 3, 1]|1|
|cc_split_swin_16h_proj_pool_512_chained_fp8|128|3|12|[12, 3, 1]|1|[16, 5, 1]|1|
|cc_split_swin_16h_proj_512_outview_wait_fp8|128|3|12|[12, 3, 1]|1|[16, 5, 1]|1|
|cc_split_swin_16h_proj_512_chained_fp8|256|2|16|[12, 3, 1]|1|[16, 5, 1]|1|
|cc_split_swin_16h_qkv_512_chained_fp8|128|2|8|[6, 3, 4]|1|[8, 5, 4]|2|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|128|3|12|[12, 3, 1]|1|[16, 5, 1]|1|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|128|3|12|[12, 3, 1]|1|[16, 5, 1]|1|
|cc_split_swin_16h_ffwd_512_chained_fp8|256|1|8|[6, 3, 2]|1|[8, 5, 2]|2|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|128|2|8|[6, 3, 2]|1|[8, 5, 2]|1|
|cc_vit_1d_projection_chained_fp8|128|3|12|[24, 1, 4]|1|[40, 1, 4]|2|
|cc_vit_1d_projection_wait_fp8|128|3|12|[24, 1, 4]|1|[40, 1, 4]|2|
|cc_vit_1d_attention_chained_fp8|128|2|8|[32, 2, 1]|1|[32, 3, 1]|1|
|cc_vit_1d_qkv_chained_fp8|128|3|12|[48, 1, 2]|1|[80, 1, 2]|2|
|cc_vit_1d_ffn_contract_chained_fp8|128|3|12|[24, 1, 4]|1|[40, 1, 4]|2|
|cc_vit_1d_ffn_expand_chained_fp8|128|3|12|[96, 1, 1]|1|[160, 1, 1]|2|
|cc_vit_1d_ffn_expand_publish_fp8|128|3|12|[96, 1, 1]|1|[160, 1, 1]|2|
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
|cc_split_swin_16h_qkv_512_chained_fp8|48|4|(1, 373)|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|0|8|(1, 91)|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|0|8|(1, 122)|
|cc_split_swin_16h_ffwd_512_chained_fp8|0|2|(1, 154)|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|0|16|(1, 518)|
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
