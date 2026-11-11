set pagination off
set confirm off
set disable-randomization off
set language c
break *main+806 if ((unsigned long)$rdx == (unsigned long)$rbp+94 || (unsigned long)$rdx == (unsigned long)$rbp+128 || (unsigned long)$rdx == (unsigned long)$rbp+246)
commands 1
silent
printf "NATIVE_STORE cell=%lu old=%u new=%u\n", ((unsigned long)$rdx-(unsigned long)$rbp)/2, (unsigned int)*(unsigned short*)$rdx, (unsigned int)((unsigned long)$rax & 65535)
continue
end
run
quit
