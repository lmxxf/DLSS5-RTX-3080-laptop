# probe_global_family: four hardware tables

Static counts cover exactly 38 launched FP8 entries. Loop observations below are inherited V2.5 semantic-loop instrumentation, not newly measured hardware-issued counts. Grid/block from V2.3 real NVAPI launches (dynamic shared=0). Occupancy is freshly queried from each actual cubin. No NCU counters are available in this experiment.

## 1. Instructions and loop evidence

|Kernel|nonNOP|HMMA|PRMT|SHF|LOP3|Historical compute loop visits/warp (720p)|
|---|---:|---:|---:|---:|---:|---|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|3042|520|132|27|151|2.0|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|2922|512|132|22|144|unrolled / no compute loop|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|3834|528|157|27|190|unrolled / no compute loop|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|3013|512|124|9|201|unrolled / no compute loop|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|4004|580|139|44|176|unrolled / no compute loop|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|3819|528|108|58|117|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|5292|552|724|58|733|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|3925|608|403|27|420|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|4895|624|443|33|492|unrolled / no compute loop|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|3906|608|395|14|409|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|5584|552|787|51|798|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|4717|544|643|23|638|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|5759|576|699|35|725|unrolled / no compute loop|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|4703|544|635|20|657|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|5843|584|857|78|873|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|4983|576|713|37|702|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|5942|592|753|67|788|unrolled / no compute loop|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|4964|576|705|38|712|unrolled / no compute loop|
|cc_split_swin_16h_final_head_512_wait_fp8|878|64|94|22|92|8.0|
|cc_split_swin_16h_proj_pool_512_chained_fp8|5605|256|360|63|605|7.0|
|cc_split_swin_16h_proj_512_outview_wait_fp8|2717|128|294|72|374|8.0|
|cc_split_swin_16h_proj_512_chained_fp8|1316|64|150|35|178|8.0|
|cc_split_swin_16h_qkv_512_chained_fp8|3775|512|260|58|233|7.0|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|2501|128|278|37|364|8.0|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|2244|128|294|38|342|8.0|
|cc_split_swin_16h_ffwd_512_chained_fp8|1199|192|116|11|114|7.0,8.0|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|2450|384|224|75|313|7.0,8.0|
|cc_vit_1d_projection_chained_fp8|2227|128|280|34|316|7.0|
|cc_vit_1d_projection_wait_fp8|2210|128|280|34|316|7.0|
|cc_vit_1d_attention_chained_fp8|2904|128|336|125|394|5.0|
|cc_vit_1d_qkv_chained_fp8|2388|192|232|20|189|15.0|
|cc_vit_1d_ffn_contract_chained_fp8|2939|256|364|34|389|15.0|
|cc_vit_1d_ffn_expand_chained_fp8|2318|128|222|17|170|16.0|
|cc_vit_1d_ffn_expand_publish_fp8|2218|128|222|13|169|16.0|
|cc_vit_1d_repack_1d_to_2d_fp8|146|0|24|17|16|unrolled / no compute loop|
|cc_vit_1d_repack_2d_to_1d_fp8|208|0|38|26|26|unrolled / no compute loop|
|cc_cb_clear|13|0|0|0|0|unrolled / no compute loop|
|cc_dec_input_upsample_1024_512_tilesync_fp8|3123|128|452|42|518|unrolled / no compute loop|

## 2. Registers and local memory

|Kernel|REG|STACK B|LOCAL B|STL|LDL|
|---|---:|---:|---:|---:|---:|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|202|0|0|0|0|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|168|0|0|0|0|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|242|0|0|0|0|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|168|48|0|8|9|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|168|24|0|5|6|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|168|40|0|8|9|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|168|24|0|3|5|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|168|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|203|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|190|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|196|0|0|0|0|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|198|0|0|0|0|
|cc_split_swin_16h_final_head_512_wait_fp8|112|0|0|0|0|
|cc_split_swin_16h_proj_pool_512_chained_fp8|162|0|0|0|0|
|cc_split_swin_16h_proj_512_outview_wait_fp8|134|0|0|0|0|
|cc_split_swin_16h_proj_512_chained_fp8|114|0|0|0|0|
|cc_split_swin_16h_qkv_512_chained_fp8|255|88|0|33|22|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|130|0|0|0|0|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|134|0|0|0|0|
|cc_split_swin_16h_ffwd_512_chained_fp8|142|0|0|0|0|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|208|0|0|0|0|
|cc_vit_1d_projection_chained_fp8|140|0|0|0|0|
|cc_vit_1d_projection_wait_fp8|138|0|0|0|0|
|cc_vit_1d_attention_chained_fp8|255|0|0|0|0|
|cc_vit_1d_qkv_chained_fp8|170|0|0|0|0|
|cc_vit_1d_ffn_contract_chained_fp8|161|0|0|0|0|
|cc_vit_1d_ffn_expand_chained_fp8|150|0|0|0|0|
|cc_vit_1d_ffn_expand_publish_fp8|142|0|0|0|0|
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
|cc_vit_1d_qkv_chained_fp8|128|2|8|[48, 1, 2]|1|[80, 1, 2]|2|
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
|cc_split_swin_16h_qkv_512_chained_fp8|48|4|(1, 632)|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|0|8|(1, 91)|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|0|8|(1, 122)|
|cc_split_swin_16h_ffwd_512_chained_fp8|0|2|(1, 285)|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|0|16|(1, 777)|
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
