# Phase15 offline input regression

Style1 Small31 Graph off; same reused input/output buffers; all input repeats deterministic. Precision comparison is NativeFP16 vs paired frozenF32 accumulation chain. Peak=1 in ENCODED working RGB, not reconstructed linearHDR. No in-game visual acceptance.

| Geometry | Input | Source class | White | PSNR peak1 dB | Maxabs | 256/400 bitdiff |
|---|---|---|---:|---:|---:|---:|
| 512 | menu-sdr-wp1 | real_game_SDR_menu | 1 | 57.033622 | 0.042611837 | 0 |
| 512 | menu-linear-wp1 | derived_display_linear_NOT_scene_HDR | 1 | 57.600389 | 0.037218660 | 0 |
| 512 | menu-linear-wp512 | derived_display_linear_NOT_scene_HDR | 512 | 57.600389 | 0.037218660 | 0 |
| 512 | menu-dynamic-wp1 | synthetic_whole_frame_transform_of_real_menu | 1 | 59.935901 | 0.040804923 | 0 |
| 512 | menu-dynamic-wp512 | synthetic_whole_frame_transform_of_real_menu | 512 | 59.935901 | 0.040804923 | 0 |
| 512 | codec-ramp-wp1 | existing_codec_synthetic_RGB_recipe | 1 | 48.229607 | 0.031194627 | 0 |
| 512 | codec-ramp-wp512 | existing_codec_synthetic_RGB_recipe | 512 | 48.229607 | 0.031194627 | 0 |
| 512 | smoke-wp1 | existing_synthetic_gradient | 1 | 57.641361 | 0.008656859 | 0 |
| 480-fit | menu-sdr-wp1 | real_game_SDR_menu | 1 | 59.558024 | 0.030074537 | 0 |
| 480-fit | menu-linear-wp1 | derived_display_linear_NOT_scene_HDR | 1 | 58.016980 | 0.044552207 | 0 |
| 480-fit | menu-linear-wp512 | derived_display_linear_NOT_scene_HDR | 512 | 58.016980 | 0.044552207 | 0 |
| 480-fit | menu-dynamic-wp1 | synthetic_whole_frame_transform_of_real_menu | 1 | 58.878775 | 0.045837343 | 0 |
| 480-fit | menu-dynamic-wp512 | synthetic_whole_frame_transform_of_real_menu | 512 | 58.878775 | 0.045837343 | 0 |
| 480-fit | codec-ramp-wp1 | existing_codec_synthetic_RGB_recipe | 1 | 50.236625 | 0.024043024 | 0 |
| 480-fit | codec-ramp-wp512 | existing_codec_synthetic_RGB_recipe | 512 | 50.236625 | 0.024043024 | 0 |
| 480-fit | smoke-wp1 | existing_synthetic_gradient | 1 | 55.851392 | 0.013289154 | 0 |
| 1024 | menu-sdr-wp1 | real_game_SDR_menu | 1 | 60.170567 | 0.045806646 | 0 |
| 1024 | menu-linear-wp1 | derived_display_linear_NOT_scene_HDR | 1 | 60.298069 | 0.034293354 | 0 |
| 1024 | menu-linear-wp512 | derived_display_linear_NOT_scene_HDR | 512 | 60.298069 | 0.034293354 | 0 |
| 1024 | menu-dynamic-wp1 | synthetic_whole_frame_transform_of_real_menu | 1 | 60.836172 | 0.029960990 | 0 |
| 1024 | menu-dynamic-wp512 | synthetic_whole_frame_transform_of_real_menu | 512 | 60.836172 | 0.029960990 | 0 |
| 1024 | codec-ramp-wp1 | existing_codec_synthetic_RGB_recipe | 1 | 46.154754 | 0.036157489 | 0 |
| 1024 | codec-ramp-wp512 | existing_codec_synthetic_RGB_recipe | 512 | 46.154754 | 0.036157489 | 0 |
| 1024 | smoke-wp1 | existing_synthetic_gradient | 1 | 60.428689 | 0.006179035 | 0 |
| 640 | menu-sdr-wp1 | real_game_SDR_menu | 1 | 59.417262 | 0.035768986 | 0 |
| 640 | menu-linear-wp1 | derived_display_linear_NOT_scene_HDR | 1 | 59.201131 | 0.026789188 | 0 |
| 640 | menu-linear-wp512 | derived_display_linear_NOT_scene_HDR | 512 | 59.201131 | 0.026789188 | 0 |
| 640 | menu-dynamic-wp1 | synthetic_whole_frame_transform_of_real_menu | 1 | 60.948154 | 0.021412313 | 0 |
| 640 | menu-dynamic-wp512 | synthetic_whole_frame_transform_of_real_menu | 512 | 60.948154 | 0.021412313 | 0 |
| 640 | codec-ramp-wp1 | existing_codec_synthetic_RGB_recipe | 1 | 49.017647 | 0.030188859 | 0 |
| 640 | codec-ramp-wp512 | existing_codec_synthetic_RGB_recipe | 512 | 49.017647 | 0.030188859 | 0 |
| 640 | smoke-wp1 | existing_synthetic_gradient | 1 | 54.310386 | 0.016964436 | 0 |
| 1152 | menu-sdr-wp1 | real_game_SDR_menu | 1 | 59.800880 | 0.030112743 | 0 |
| 1152 | menu-linear-wp1 | derived_display_linear_NOT_scene_HDR | 1 | 59.046331 | 0.031900406 | 0 |
| 1152 | menu-linear-wp512 | derived_display_linear_NOT_scene_HDR | 512 | 59.046331 | 0.031900406 | 0 |
| 1152 | menu-dynamic-wp1 | synthetic_whole_frame_transform_of_real_menu | 1 | 60.918860 | 0.038248837 | 0 |
| 1152 | menu-dynamic-wp512 | synthetic_whole_frame_transform_of_real_menu | 512 | 60.918860 | 0.038248837 | 0 |
| 1152 | codec-ramp-wp1 | existing_codec_synthetic_RGB_recipe | 1 | 49.071551 | 0.028471828 | 0 |
| 1152 | codec-ramp-wp512 | existing_codec_synthetic_RGB_recipe | 512 | 49.071551 | 0.028471828 | 0 |
| 1152 | smoke-wp1 | existing_synthetic_gradient | 1 | 56.147145 | 0.013126671 | 0 |
| 720 | menu-sdr-wp1 | real_game_SDR_menu | 1 | 60.247254 | 0.043955266 | 0 |
| 720 | menu-linear-wp1 | derived_display_linear_NOT_scene_HDR | 1 | 60.773320 | 0.027213454 | 0 |
| 720 | menu-linear-wp512 | derived_display_linear_NOT_scene_HDR | 512 | 60.773320 | 0.027213454 | 0 |
| 720 | menu-dynamic-wp1 | synthetic_whole_frame_transform_of_real_menu | 1 | 61.727794 | 0.036622822 | 0 |
| 720 | menu-dynamic-wp512 | synthetic_whole_frame_transform_of_real_menu | 512 | 61.727794 | 0.036622822 | 0 |
| 720 | codec-ramp-wp1 | existing_codec_synthetic_RGB_recipe | 1 | 47.234802 | 0.037009418 | 0 |
| 720 | codec-ramp-wp512 | existing_codec_synthetic_RGB_recipe | 512 | 47.234802 | 0.037009418 | 0 |
| 720 | smoke-wp1 | existing_synthetic_gradient | 1 | 60.564907 | 0.007144094 | 0 |
| 1024-square | menu-sdr-wp1 | real_game_SDR_menu | 1 | 60.881225 | 0.036385596 | 0 |
| 1024-square | menu-linear-wp1 | derived_display_linear_NOT_scene_HDR | 1 | 60.648979 | 0.031277061 | 0 |
| 1024-square | menu-linear-wp512 | derived_display_linear_NOT_scene_HDR | 512 | 60.648979 | 0.031277061 | 0 |
| 1024-square | menu-dynamic-wp1 | synthetic_whole_frame_transform_of_real_menu | 1 | 60.356200 | 0.040896893 | 0 |
| 1024-square | menu-dynamic-wp512 | synthetic_whole_frame_transform_of_real_menu | 512 | 60.356200 | 0.040896893 | 0 |
| 1024-square | codec-ramp-wp1 | existing_codec_synthetic_RGB_recipe | 1 | 43.436806 | 0.054382861 | 0 |
| 1024-square | codec-ramp-wp512 | existing_codec_synthetic_RGB_recipe | 512 | 43.436806 | 0.054382861 | 0 |
| 1024-square | smoke-wp1 | existing_synthetic_gradient | 1 | 61.071690 | 0.006017804 | 0 |

Legacy45dB is NOT declared passed globally: accepted canonical720 remains43.577948dB. A single menu and synthetic patterns cannot establish overall image quality.

New correctness issues: `[]`. White1/512 encoded inputs and all corresponding outputs are bit-identical. Real linearHDR/gameplay sequence evidence remains missing; performance work paused.
