/* Independent classic Malbolge (3^10) interpreter.
   Written from the published semantics: 94-symbol alphabet, crazy/rot ops,
   xlat1 encryption after every step. No code taken from the target repo. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define N 59049
#define TRITS 10

static unsigned mem[N];

static const char *XLAT1 =
"5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@";

static int enc[128];

static unsigned crazy(unsigned x, unsigned y, int flip){
    unsigned r=0,p=1;
    for(int i=0;i<TRITS;i++){
        unsigned a=x%3, b=y%3, t;
        /* table[y][x] = {{1,0,0},{1,0,2},{2,2,1}}  (flip swaps roles) */
        static const int T[3][3]={{1,0,0},{1,0,2},{2,2,1}};
        t = flip ? T[a][b] : T[b][a];
        r += t*p;
        x/=3; y/=3; p*=3;
    }
    return r;
}

static unsigned crazyd(unsigned x, unsigned y){ return crazy(x,y,0); }

int main(int argc,char**argv){
    if(argc<2){fprintf(stderr,"usage: %s prog.mb [max_steps] [flip]\n",argv[0]);return 2;}
    int flip = argc>3 ? atoi(argv[3]) : 0;
    long long maxsteps = argc>2 ? atoll(argv[2]) : 2000000000LL;

    for(int i=0;i<94;i++) enc[33+i]=(unsigned char)XLAT1[i];

    FILE*f=fopen(argv[1],"rb"); if(!f){perror("open");return 1;}
    int ch; long n=0;
    while((ch=fgetc(f))!=EOF){
        if(isspace(ch)) continue;
        if(ch<33||ch>126){fprintf(stderr,"bad char %d at %ld\n",ch,n);return 1;}
        if(n>=N){fprintf(stderr,"too long\n");return 1;}
        mem[n++]=(unsigned)ch;
    }
    fclose(f);
    for(long i=n;i<N;i++) mem[i]= crazyd(mem[i-1],mem[i-2]);

    unsigned a=0,c=0,d=0;
    long long steps=0;
    unsigned char *out=malloc(1<<20); size_t on=0, ocap=1<<20;
    int status=0;
    while(steps<maxsteps){
        steps++;
        unsigned instr=(mem[c]+c)%94;
        switch(instr){
            case 4:  c=mem[d]; break;
            case 5:
                if(on==ocap){ocap*=2;out=realloc(out,ocap);}
                out[on++]=(unsigned char)(a&0xFF); break;
            case 23: a=0xFFFFFFFFu; break;      /* no stdin */
            case 39: mem[d]=mem[d]/3 + (mem[d]%3)*19683u; a=mem[d]; break;
            case 40: d=mem[d]; break;
            case 62: mem[d]=crazyd(a,mem[d]); a=mem[d]; break;
            case 68: break;
            case 81: status=1; goto done;
            default: break;                     /* undefined instr: no-op */
        }
        if(mem[c]>=33&&mem[c]<=126) mem[c]=(unsigned)enc[mem[c]];
        c=(c+1)%N; d=(d+1)%N;
    }
done:
    fwrite(out,1,on,stdout);
    fflush(stdout);
    fprintf(stderr,"steps: %lld | status: %s | out_bytes: %zu | src_cells: %ld\n",
            steps, status?"HALTED":"MAX_STEPS", on, n);
    return 0;
}
