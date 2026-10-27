# V2.8 resource controls

|Case|Kernel|REG before→after|STACK before→after B|Warps/SM before→after|LDL/STL after|
|---|---|---:|---:|---:|---:|
|vit_cq|cc_vit_1d_ffn_contract_chained_fp8|179→166|0→0|8→12|0/0|
|vit_cq|cc_vit_1d_qkv_chained_fp8|197→168|0→64|8→12|16/18|
|vit_cqe|cc_vit_1d_ffn_contract_chained_fp8|179→166|0→0|8→12|0/0|
|vit_cqe|cc_vit_1d_qkv_chained_fp8|197→168|0→64|8→12|16/18|
|vit_cqe|cc_vit_1d_ffn_expand_publish_fp8|202→168|0→168|8→12|61/53|
|vit_cqe|cc_vit_1d_ffn_expand_chained_fp8|204→168|0→160|8→12|59/55|
|vit_contract|cc_vit_1d_ffn_contract_chained_fp8|179→166|0→0|8→12|0/0|
|head|cc_split_swin_16h_final_head_512_wait_fp8|136→128|0→136|8→16|42/40|
|pool|cc_split_swin_16h_proj_pool_512_chained_fp8|180→164|0→0|8→12|0/0|
|proj|cc_split_swin_16h_proj_512_chained_fp8|141→128|0→128|8→16|43/38|
|ffwd_proj|cc_split_swin_16h_ffwd_proj_512_chained_fp8|204→168|0→208|8→12|74/69|
|ffwd_proj_inp|cc_split_swin_16h_ffwd_proj_inpview_512_chained_fp8|205→168|0→208|8→12|73/69|
|ffwd_inp|cc_split_swin_16h_ffwd_inpview_512_tilesync_fp8|212→168|0→120|8→12|26/41|
|up|cc_tinlayout_fused_swin_1h_32_1_upsample_tilesync_fp8|212→168|0→56|8→12|13/13|
