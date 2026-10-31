# Half-step pool source audit

38 launched FP8 kernels; zero means no MMA run (standalone UP). Peak is allocated virtual b32 pool per run, not physical registers.

|Kernel|Old peak|Split peak|Runs|Single-use encoded operands|Backup moves|
|---|---:|---:|---:|---:|---:|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|16|16|18|8|0|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|24|24|17|0|0|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|24|24|18|16|0|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|24|24|17|0|0|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|16|16|17|0|0|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|16|16|17|0|0|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|56|56|16|8|0|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|56|56|23|0|0|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|56|56|25|16|0|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|56|56|23|0|0|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|56|56|20|8|0|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|56|56|19|0|0|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|56|56|23|32|0|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|56|56|19|0|0|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|56|56|15|8|0|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|56|56|14|0|0|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|56|56|16|16|0|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|56|56|14|0|0|
|cc_split_swin_16h_final_head_512_wait_fp8|72|70|1|0|0|
|cc_split_swin_16h_proj_pool_512_chained_fp8|80|80|2|0|0|
|cc_split_swin_16h_proj_512_outview_wait_fp8|80|80|1|0|0|
|cc_split_swin_16h_proj_512_chained_fp8|72|70|1|0|0|
|cc_split_swin_16h_qkv_512_chained_fp8|112|112|6|0|0|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|80|80|1|0|0|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|80|80|1|0|0|
|cc_split_swin_16h_ffwd_512_chained_fp8|72|70|5|0|0|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|80|80|5|0|0|
|cc_vit_1d_projection_chained_fp8|40|40|2|0|0|
|cc_vit_1d_projection_wait_fp8|40|40|2|0|0|
|cc_vit_1d_attention_chained_fp8|40|40|2|0|0|
|cc_vit_1d_qkv_chained_fp8|56|56|2|0|0|
|cc_vit_1d_ffn_contract_chained_fp8|80|80|2|0|0|
|cc_vit_1d_ffn_expand_chained_fp8|80|80|1|0|0|
|cc_vit_1d_ffn_expand_publish_fp8|80|80|1|0|0|
|cc_vit_1d_repack_1d_to_2d_fp8|0|0|0|0|0|
|cc_vit_1d_repack_2d_to_1d_fp8|0|0|0|0|0|
|cc_cb_clear|0|0|0|0|0|
|cc_dec_input_upsample_1024_512_tilesync_fp8|20|18|2|128|0|
