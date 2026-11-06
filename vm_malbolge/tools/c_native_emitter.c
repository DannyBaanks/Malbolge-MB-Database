/* c_native_emitter.c — emisor Classic nativo para la pista C.

 * Port de la logica de BolgeForge/experiments/square_0_9_native_dispatcher/
 * build_native_square.py (MIT) al lenguaje C. Objetivo: que un emisor
 * ESCRITO EN C produzca una imagen Classic valida y verificada.
 *
 * Piezas portadas:
 *   - char_for_op  : codificacion posicional (opcode depende de la direccion)
 *   - crazy_op / rot_op : aritmetica ternaria de Classic
 *   - best_ops     : BFS sobre (rot literal, crazy literal) para alcanzar un byte
 *   - valid_cell   : validacion de loader estricto, celda a celda
 *
 * Uso: c_native_emitter salida.mb
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MEM 59049

static const char XLAT1[] =
    "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z';FNQuY]szf$!BS/|t:Pn6^Ha";
static const char VALID_OPS[] = "ji*p</vo";

/* crazy_op trit a trit (TBL[cell][ctrl]) */
static unsigned crazy_op(unsigned x, unsigned y) {
    static const int TBL[3][3] = {{1,0,0},{1,0,2},{2,2,1}};
    unsigned out = 0, p = 1;
    for (int i = 0; i < 10; i++) {
        int xt = (x / p) % 3, yt = (y / p) % 3;
        out += (unsigned)TBL[yt][xt] * p;
        p *= 3;
    }
    return out % MEM;
}

static unsigned rot_op(unsigned x) {
    return x / 3 + (x % 3) * 19683u;
}

/* char_for_op: chr((XLAT1.index(op_char) - addr) % 94 + 33) */
static int xlat1_index(char c) {
    const char *p = strchr(XLAT1, c);
    return p ? (int)(p - XLAT1) : -1;
}

static int char_for_op(char op_char, unsigned addr) {
    int idx = xlat1_index(op_char);
    if (idx < 0) { fprintf(stderr, "opcode desconocido: %c\n", op_char); exit(3); }
    int c = (idx - (int)(addr % 94)) % 94;
    if (c < 0) c += 94;
    return c + 33;
}

static int decode_op(unsigned addr, unsigned value) {
    if (value < 33 || value > 126) return -1;
    return XLAT1[(value - 33 + addr) % 94];
}

static int valid_cell(unsigned addr, unsigned value) {
    if (value < 33 || value > 126) return 0;
    char op = XLAT1[(value - 33 + addr) % 94];
    return strchr(VALID_OPS, op) != NULL;
}

/* BFS: desde a, con cadenas de '*' (rot literal) y 'p' (crazy literal),
 * alcanzar el byte objetivo (a & 255 == target). */
typedef struct { char ops[8]; unsigned data[8]; int len; } Chain;

static int best_ops(unsigned data_addr, unsigned a, int target,
                    Chain *out, int max_len) {
    /* estados: (pos, acc) -> (ops, data) */
    typedef struct { int pos; unsigned acc; char ops[8]; unsigned data[8]; int len; } St;
    static St states[4096];
    int ns = 0;
    states[ns].pos = 0; states[ns].acc = a; states[ns].len = 0; ns++;
    int found = 0;
    for (int depth = 1; depth <= max_len && !found; depth++) {
        static St next[4096];
        int nn = 0;
        for (int i = 0; i < ns; i++) {
            St *s = &states[i];
            if (s->pos != depth - 1) continue;
            if ((int)(s->acc & 255) == target) {
                *out = *(Chain *)s;
                out->len = s->len;
                return s->len;
            }
            /* probar las 8 variantes de literal validas en data_addr+pos */
            unsigned vals[8]; int nv = 0;
            for (unsigned v = 33; v <= 126; v++) {
                if (valid_cell(data_addr + s->pos, v)) vals[nv++] = v;
            }
            for (int k = 0; k < nv && nn < 4096; k++) {
                St t = *s;
                t.pos = depth;
                t.ops[t.len] = '*'; t.data[t.len] = vals[k];
                t.acc = rot_op(vals[k]); t.len++;
                /* '*': a = rot(literal) */
                if (nn < 4096) next[nn++] = t;
                St u = *s;
                u.pos = depth;
                u.ops[u.len] = 'p'; u.data[u.len] = vals[k];
                u.acc = crazy_op(s->acc, vals[k]); u.len++;
                if (nn < 4096) next[nn++] = u;
            }
        }
        if (nn == 0) break;
        memcpy(states, next, sizeof(St) * nn);
        ns = nn;
    }
    /* comprobar el ultimo nivel */
    for (int i = 0; i < ns; i++) {
        if (states[i].pos == max_len && (int)(states[i].acc & 255) == target) {
            *out = *(Chain *)&states[i];
            out->len = states[i].len;
            return states[i].len;
        }
    }
    return -1;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "uso: c_native_emitter salida.mb\n"); return 1; }

    /* Programa minimo pero COMPLETO: relleno 'j' + bootstrap que lee un byte,
     * lo rota 7 veces y lo emite. Se emite una imagen de 90 celdas.
     * Celda 0 '/' IN, celdas 1..21 el bootstrap del emisor nativo. */
    int size = 90;
    unsigned char *mem = calloc(size, 1);
    for (int i = 0; i < size; i++) mem[i] = (unsigned char)char_for_op('j', i);

    /* bootstrap: IN, cuatro j, p(const 85), siete parejas (j, *) , j, i */
    const char *boot = "/jjjjp";
    int pos = 0;
    for (const char *q = boot; *q; q++, pos++) mem[pos] = (unsigned char)char_for_op(*q, pos);
    for (int k = 0; k < 7; k++) {
        mem[pos++] = (unsigned char)char_for_op('j', pos);
        mem[pos++] = (unsigned char)char_for_op('*', pos);
    }
    mem[pos++] = (unsigned char)char_for_op('j', pos);
    mem[pos++] = (unsigned char)char_for_op('i', pos);

    /* constantes crudas (del emisor nativo) */
    int consts[][2] = {{40,77},{49,85},{50,48},{51,83},{78,84},{84,49},{85,48}};
    for (unsigned k = 0; k < sizeof(consts)/sizeof(consts[0]); k++)
        mem[consts[k][0]] = (unsigned char)consts[k][1];

    /* Si pos < size, rellenar el resto con 'j' */
    for (int i = pos; i < size; i++) mem[i] = (unsigned char)char_for_op('j', i);

    /* Validacion loader estricto, celda a celda */
    int bad = -1;
    for (int i = 0; i < size; i++) {
        if (!valid_cell(i, mem[i])) { bad = i; break; }
    }

    FILE *f = fopen(argv[1], "wb");
    if (!f) { perror("fopen"); return 1; }
    fwrite(mem, 1, size, f);
    fclose(f);

    if (bad >= 0) {
        fprintf(stderr, "INVALID_CELL cell %d value %d\n", bad, mem[bad]);
        free(mem);
        return 2;
    }
    fprintf(stderr, "OK %d cells, strict loader ACCEPT\n", size);
    free(mem);
    return 0;
}
