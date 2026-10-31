# V3.3 source temporary pool peaks

Each cell is the max virtual b32 decoder pool per MMA run, not total physical registers. Raw snapshots are counted separately. Phase-pass exactly preserves total half-decode events.

|Kernel|Baseline|Phase-pass|Remat spill|Phase guarded|
|---|---:|---:|---:|---:|
|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|16|8|16|8|
|cc_tinlayout_fused_swin_1h_32_1_outview_wait_fp8|24|12|24|24|
|cc_tinlayout_fused_swin_1h_32_1_ds_wait_fp8|24|12|24|24|
|cc_tinlayout_fused_swin_1h_32_1_inpview_tilesync_fp8|24|12|24|24|
|cc_tinlayout_fused_post_block_swin_1h_32_fp8|16|8|16|8|
|cc_tinlayout_fused_pre_block_swin_1h_32_1_ds_fp8|16|8|16|16|
|cc_tinlayout_fused_swin_2h_64_2_upsample_tilesync_fp8|56|28|6|56|
|cc_tinlayout_fused_swin_2h_64_2_outview_wait_fp8|56|28|6|56|
|cc_tinlayout_fused_swin_2h_64_2_ds_wait_fp8|56|28|6|56|
|cc_tinlayout_fused_swin_2h_64_2_inpview_tilesync_fp8|56|28|6|56|
|cc_tinlayout_fused_swin_4h_128_4_upsample_tilesync_fp8|56|28|56|56|
|cc_tinlayout_fused_swin_4h_128_4_outview_wait_fp8|56|28|56|28|
|cc_tinlayout_fused_swin_4h_128_4_ds_wait_fp8|56|28|56|28|
|cc_tinlayout_fused_swin_4h_128_4_inpview_tilesync_fp8|56|28|56|28|
|cc_tinlayout_fused_swin_8h_256_8_upsample_tilesync_fp8|56|28|56|28|
|cc_tinlayout_fused_swin_8h_256_8_outview_wait_fp8|56|28|56|28|
|cc_tinlayout_fused_swin_8h_256_8_ds_wait_fp8|56|28|56|28|
|cc_tinlayout_fused_swin_8h_256_8_inpview_tilesync_fp8|56|28|56|28|
|cc_split_swin_16h_final_head_512_wait_fp8|72|20|72|20|
|cc_split_swin_16h_proj_pool_512_chained_fp8|80|20|80|20|
|cc_split_swin_16h_proj_512_outview_wait_fp8|80|20|80|20|
|cc_split_swin_16h_proj_512_chained_fp8|72|20|72|20|
|cc_split_swin_16h_qkv_512_chained_fp8|112|28|6|112|
|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|80|20|80|20|
|cc_split_swin_16h_ffwd_proj_512_chained_fp8|80|20|80|20|
|cc_split_swin_16h_ffwd_512_chained_fp8|72|20|72|20|
|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|80|20|80|80|
|cc_vit_1d_projection_chained_fp8|40|20|40|20|
|cc_vit_1d_projection_wait_fp8|40|20|40|20|
|cc_vit_1d_attention_chained_fp8|40|20|40|20|
|cc_vit_1d_qkv_chained_fp8|56|28|56|56|
|cc_vit_1d_ffn_contract_chained_fp8|80|20|80|20|
|cc_vit_1d_ffn_expand_chained_fp8|80|20|80|20|
|cc_vit_1d_ffn_expand_publish_fp8|80|20|80|20|
|cc_vit_1d_repack_1d_to_2d_fp8|0|0|0|0|
|cc_vit_1d_repack_2d_to_1d_fp8|0|0|0|0|
|cc_cb_clear|0|0|0|0|
|cc_dec_input_upsample_1024_512_tilesync_fp8|20|6|20|6|
