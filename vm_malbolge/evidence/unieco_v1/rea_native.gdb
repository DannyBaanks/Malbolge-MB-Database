set pagination off
set confirm off
set disable-randomization off
break *main+806 if ($rdx == $rbp+94 || $rdx == $rbp+128 || $rdx == $rbp+246)
commands 1
silent
printf "NATIVE_STORE cell=%ld old=%u new=%u\n", ($rdx-$rbp)/2, *(unsigned short*)$rdx, $rax & 0xffff
continue
end
run
quit
