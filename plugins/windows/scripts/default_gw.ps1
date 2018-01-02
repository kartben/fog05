# param (
#    [Parameter(Mandatory=$true)][string]$addr
# )
#$addr='192.168.1.148';
#write-output $addr
#$name = get-wmiobject Win32_NetworkAdapterConfiguration |? {$_.ipaddress -contains $addr} | % {$_.GetRelated("win32_NetworkAdapter")} | select NetConnectionID |%{$_.NetConnectionID};
$name = get-wmiobject Win32_NetworkAdapterConfiguration |? {$_.defaultipgateway} | % {$_.GetRelated("win32_NetworkAdapter")} | select NetConnectionID |%{$_.NetConnectionID};
write-output $name