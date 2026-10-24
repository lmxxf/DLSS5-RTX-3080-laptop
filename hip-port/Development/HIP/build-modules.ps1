# 2026-09-17: superseded by ..\..\hip\build-modules.ps1 (production recipe, explicit defines). Kept for the experiment
# scripts that call it; the kernel sources moved to hip\, so pass -SourceDir accordingly.
param(
    [Parameter(Mandatory=$true)][string]$Compiler,
    [Parameter(Mandatory=$true)][string]$OutputDir,
    [string]$SourceDir = $PSScriptRoot,
    [switch]$IsaHalf,
    [switch]$Fast,
    [switch]$VitExpandPair
)
$ErrorActionPreference = 'Stop'
$OutputDir = [IO.Path]::GetFullPath($OutputDir)
New-Item -ItemType Directory -Force $OutputDir | Out-Null
$utf8 = New-Object Text.UTF8Encoding($false)
$modules = @(
    @('c32_prefix_reference', @('c32_reference.hip', 'prefix_reference.hip')),
    @('multihead-reference', @('multihead_reference.hip')),
    @('deep_reference', @('deep_reference.hip')),
    @('boundary_reference', @('boundary_reference.hip')),
    @('c32_wmma', @('c32_wmma.hip')),
    @('multihead-wmma', @('multihead_wmma.hip')),
    @('deep_wmma', @('deep_wmma.hip')),
    @('wave-pointwise', @('c32_reference.hip', 'wave_pointwise.hip')),
    @('c32_tiled', @('c32_tiled.hip')),
    @('multihead-tiled', @('multihead_tiled.hip'))
)
if ($Fast) {
    $modules += @(
        @('c32_fast', @('c32_fast.hip')),
        @('c32_fast_attention', @('c32_fast_attention.hip')),
        @('boundary-fast', @('c32_fast_attention.hip', 'boundary_fast.hip')),
        @('c32_fused_attention', @('c32_fused_attention_packed.hip')),
        @('c32_fused_ffn_attention', @('c32_fused_ffn_attention.hip')),
        @('c32_fused_ffn_attention-packed', @('c32_fused_ffn_attention.hip')),
        @('prefix_fast', @('prefix_fast.hip')),
        @('multihead-fast', @('multihead_fast.hip')),
        @('multihead-fast-padded-wave', @('multihead_fast_padded.hip')),
        @('multihead_fused_attention', @('multihead_fused_attention.hip')),
        @('deep_fast', @('deep_fast.hip')),
        @('deep_fast-packed', @('deep_fast.hip')),
        @('multihead-fast-packed', @('multihead_fast.hip')),
        @('multihead-fast-padded-wave-packed', @('multihead_fast_padded.hip'))
    )
}
$manifest = @()
foreach ($module in $modules) {
    $source = if ($IsaHalf) { "#define HIP_ISA_HALF 1`n" } else { '' }
    if ($module[0] -like '*-packed') { $source += "#define HIP_PREPACKED_WEIGHTS 1`n" }
    if ($VitExpandPair -and $module[0] -like 'deep_fast*') { $source += "#define HIP_VIT_EXPAND_PAIR 1`n" }
    foreach ($part in $module[1]) {
        $source += [IO.File]::ReadAllText((Join-Path $SourceDir $part)) + "`n"
    }
    $sourcePath = Join-Path $OutputDir ($module[0] + '.generated.hip')
    [IO.File]::WriteAllText($sourcePath, $source, $utf8)
    & $Compiler (Join-Path $OutputDir ($module[0] + '.hsaco')) $sourcePath comgr
    if ($LASTEXITCODE -ne 0) { throw "COMGR failed: $($module[0])" }
    $manifest += [pscustomobject]@{
        module = $module[0]
        source_sha256 = (Get-FileHash $sourcePath -Algorithm SHA256).Hash
        code_sha256 = (Get-FileHash (Join-Path $OutputDir ($module[0] + '.hsaco')) -Algorithm SHA256).Hash
    }
}

[IO.File]::WriteAllText((Join-Path $OutputDir 'modules.json'), ($manifest | ConvertTo-Json -Depth 3), $utf8)
