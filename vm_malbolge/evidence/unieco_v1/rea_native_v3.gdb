set pagination off
set confirm off
set disable-randomization off
set language c
break *main+806 if ((unsigned long)$rdx == (unsigned long)$rbp+94 || (unsigned long)$rdx == (unsigned long)$rbp+128 || (unsigned long)$rdx == (unsigned long)$rbp+246)
commands 1
silent
printf "BEFORE cell=%lu old=%u pending=%u\n", ((unsigned long)$rdx-(unsigned long)$rbp)/2, (unsigned int)*(unsigned short*)$rdx, (unsigned int)((unsigned long)$rax & 65535)
continue
end
break *main+809 if ((unsigned long)$rdx == (unsigned long)$rbp+94 || (unsigned long)$rdx == (unsigned long)$rbp+128 || (unsigned long)$rdx == (unsigned long)$rbp+246)
commands 2
silent
printf "AFTER cell=%lu actual=%u\n", ((unsigned long)$rdx-(unsigned long)$rbp)/2, (unsigned int)*(unsigned short*)$rdx
continue
end
run
quit
