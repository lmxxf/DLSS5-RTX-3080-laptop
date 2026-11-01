param([string]$InputPath)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$ErrorActionPreference='Stop'
$inputData=Get-Content -LiteralPath $InputPath -Raw -Encoding UTF8 | ConvertFrom-Json
$results=@()
foreach($item in $inputData.files) {
 $h=(Get-FileHash -LiteralPath $item.Path -Algorithm SHA256).Hash.ToLowerInvariant()
 if($h -ne $item.Expected){throw ('SHA mismatch: '+$item.Path)}
 $sig=$null
 if($item.Kind -eq 'PE'){$sig=(Get-AuthenticodeSignature -LiteralPath $item.Path).Status.ToString()}
 $results += [pscustomobject]@{Label=$item.Label;Path=$item.Path;SHA256=$h;Authenticode=$sig;Kind=$item.Kind}
}
$results | ConvertTo-Json -Depth 5
