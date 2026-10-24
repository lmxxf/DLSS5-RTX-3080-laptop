// Candidate game boundary: exact-size RGB texture, no resize or color transform.
// Host must validate a single-sample 1920x1080 float-compatible SRV and synchronize
// texture ownership before dispatch. Padding matches the controlled RGB contract;
// actual game color-space and optional texture contracts require separate proof.
Texture2D<float4> source : register(t0);
RWStructuredBuffer<float4> tiles : register(u0);
RWStructuredBuffer<float4> post_base : register(u1);

[numthreads(8,8,1)]
void main(uint3 group : SV_GroupID, uint3 lane : SV_GroupThreadID) {
    uint width,height; source.GetDimensions(width,height);
#ifdef NATIVE_RGB_PROCESSING_HEIGHT // DLSS5_NETWORK_FREE_RES: the host passes the padded height
    uint processing_height=NATIVE_RGB_PROCESSING_HEIGHT;
#else
    uint processing_height=((height+127)/128)*128;
#endif
#ifdef NATIVE_RGB_PROCESSING_WIDTH
    uint processing_width=NATIVE_RGB_PROCESSING_WIDTH;
#else
    uint processing_width=width;
#endif
    uint2 p = group.xy * 8 + lane.xy;
    if (p.x >= processing_width || p.y >= processing_height) return;
    uint sy = p.y < height ? p.y : 2*height-2-p.y;
    uint sx=p.x<width?p.x:2*width-2-p.x;
    float4 pixel = source.Load(int3(sx, sy, 0));
#if !NATIVE_RGB_NO_TILES // HIP backend: the tile-ordered copy is never read
    uint tile = group.y * (processing_width/8) + group.x;
    tiles[tile * 64 + lane.y * 8 + lane.x] = pixel;
#endif
    post_base[p.y * processing_width + p.x] = pixel;
}
