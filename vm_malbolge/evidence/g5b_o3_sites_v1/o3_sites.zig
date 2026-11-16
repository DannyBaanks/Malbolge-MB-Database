//! G5b O3: ¿cuántos sitios de código pueden compartir una celda de datos T?
//!
//! Uso: o3_sites <ruta/olmstead_original.c>
//! Lee xlat1/xlat2 del C del vendor (fuente independiente del Python del repo).
//!
//! Modelo (Olmstead Classic, ver g5b_orbit_lemmas_v1 y ATTEMPT01_OBSTRUCTION):
//! - Una celda ejecutada en cada pasada recorre toda su órbita xlat2; sólo es
//!   relleno válido si su palabra inicial carga como 'o' y toda la órbita es NOP
//!   (residuo "persistente").
//! - Un sitio que lee d en la celda T (ROT/MOVD/CRAZY) se alcanza tras un JMP que
//!   lee q; con k celdas ejecutadas no-d entre el aterrizaje y el op, T = q+1+k,
//!   así que delta_in = k+1. Tras el op, j-1 celdas no-d y luego un lector de d
//!   (un JMP cabe en cualquier residuo) en T+j: delta_out = j.
//! - Dos sitios distintos sobre la misma T necesitan delta_in distintos (si no,
//!   comparten celda de entrada) y delta_out distintos (si no, comparten
//!   continuación). Máximo de sitios = emparejamiento bipartito máximo.
//! Modo estricto: relleno = sólo NOP persistente. Modo laxo: también celdas
//! IN/OUT de un solo activo (disparan E/S en su pasada activa).
const std = @import("std");

const EFFECT = "ji*p</v";
const VALID = "ji*p</vo";

fn isIn(c: u8, set: []const u8) bool {
    return std.mem.indexOfScalar(u8, set, c) != null;
}

fn parseTable(src: []const u8, name: []const u8, out: *[94]u8) !void {
    var key_buf: [32]u8 = undefined;
    const key = try std.fmt.bufPrint(&key_buf, "{s}[] =", .{name});
    var i = (std.mem.indexOf(u8, src, key) orelse return error.TableNotFound) + key.len;
    var n: usize = 0;
    while (i < src.len and src[i] != ';') : (i += 1) {
        if (src[i] != '"') continue;
        i += 1;
        while (src[i] != '"') : (i += 1) {
            var c = src[i];
            if (c == '\\') {
                i += 1;
                c = switch (src[i]) {
                    '\\' => '\\',
                    '"' => '"',
                    '\'' => '\'',
                    else => return error.UnsupportedEscape,
                };
            }
            if (n >= 94) return error.TableTooLong;
            out[n] = c;
            n += 1;
        }
    }
    if (n != 94) return error.TableWrongLength;
}

const Tables = struct {
    x1: [94]u8,
    x2: [94]u8,

    fn succ(t: *const Tables, w: u8) u8 {
        return t.x2[w - 33];
    }
    fn dec(t: *const Tables, w: u8, r: usize) u8 {
        return t.x1[(@as(usize, w) - 33 + r) % 94];
    }
    /// Escribe la órbita de w en buf; devuelve su longitud.
    fn orbit(t: *const Tables, w: u8, buf: *[94]u8) usize {
        var n: usize = 0;
        var v = w;
        while (true) {
            buf[n] = v;
            n += 1;
            v = t.succ(v);
            if (v == w) return n;
        }
    }
};

const OPS = "*jp/<"; // ROT MOVD CRAZY IN OUT
const OP_NAMES = [_][]const u8{ "ROT", "MOVD", "CRAZY", "IN", "OUT" };
const D_OPS = 3; // los tres primeros leen d

const Analysis = struct {
    persistent: [94]bool = @splat(false),
    // single[op][r]: máscara de longitudes de órbita (bit L) con un solo activo == op
    single: [OPS.len][94]u128 = @splat(@splat(0)),
    sum_orbit_len: usize = 0,
    n_orbits: usize = 0,
};

fn analyse(t: *const Tables) Analysis {
    var a: Analysis = .{};
    var buf: [94]u8 = undefined;
    var seen: [127]bool = @splat(false);
    var w: u8 = 33;
    while (w <= 126) : (w += 1) {
        if (!seen[w]) {
            const n = t.orbit(w, &buf);
            for (buf[0..n]) |v| seen[v] = true;
            a.sum_orbit_len += n;
            a.n_orbits += 1;
        }
    }
    for (0..94) |r| {
        w = 33;
        while (w <= 126) : (w += 1) {
            const n = t.orbit(w, &buf);
            const first = t.dec(w, r);
            if (!isIn(first, VALID)) continue;
            var n_eff: usize = 0;
            var eff: u8 = 0;
            for (buf[0..n]) |v| {
                const c = t.dec(v, r);
                if (isIn(c, EFFECT)) {
                    n_eff += 1;
                    eff = c;
                }
            }
            if (n_eff == 0 and first == 'o') a.persistent[r] = true;
            if (n_eff == 1) {
                if (std.mem.indexOfScalar(u8, OPS, eff)) |oi| a.single[oi][r] |= @as(u128, 1) << @intCast(n);
            }
        }
    }
    return a;
}

fn nonD(a: *const Analysis, r: usize, lax: bool) bool {
    if (a.persistent[r]) return true;
    if (!lax) return false;
    return a.single[3][r] != 0 or a.single[4][r] != 0;
}

fn runLen(a: *const Analysis, r: usize, dir: i32, lax: bool) usize {
    var k: usize = 0;
    var p: i64 = @intCast(r);
    while (k < 93) {
        p = @mod(p + dir, 94);
        if (!nonD(a, @intCast(p), lax)) break;
        k += 1;
    }
    return k;
}

const MAXD = 96;

/// Emparejamiento bipartito máximo (Kuhn) entre delta_in y delta_out.
fn tryAug(u: usize, adj: *const [MAXD][MAXD]bool, vis: *[MAXD]bool, match_r: *[MAXD]i32) bool {
    for (0..MAXD) |v| {
        if (!adj[u][v] or vis[v]) continue;
        vis[v] = true;
        if (match_r[v] < 0 or tryAug(@intCast(match_r[v]), adj, vis, match_r)) {
            match_r[v] = @intCast(u);
            return true;
        }
    }
    return false;
}

fn maxSites(a: *const Analysis, lax: bool, op_mask: u8, pairs_out: *[MAXD][MAXD]bool) usize {
    pairs_out.* = @splat(@splat(false));
    for (0..D_OPS) |oi| {
        if (op_mask & (@as(u8, 1) << @intCast(oi)) == 0) continue;
        for (0..94) |r| {
            if (a.single[oi][r] == 0) continue;
            const kin = runLen(a, r, -1, lax);
            const kout = runLen(a, r, 1, lax);
            for (1..kin + 2) |din| for (1..kout + 2) |dout| {
                pairs_out[din][dout] = true;
            };
        }
    }
    var match_r: [MAXD]i32 = @splat(-1);
    var count: usize = 0;
    for (0..MAXD) |u| {
        var vis: [MAXD]bool = @splat(false);
        if (tryAug(u, pairs_out, &vis, &match_r)) count += 1;
    }
    return count;
}

pub fn main(init: std.process.Init) !void {
    const io = init.io;
    const arena = init.arena.allocator();
    const args = try init.minimal.args.toSlice(arena);
    if (args.len != 2) {
        std.log.err("uso: {s} <olmstead_original.c>", .{args[0]});
        std.process.exit(2);
    }
    const src = try std.Io.Dir.cwd().readFileAlloc(io, args[1], arena, .limited(1 << 20));
    var t: Tables = undefined;
    try parseTable(src, "xlat1", &t.x1);
    try parseTable(src, "xlat2", &t.x2);

    const a = analyse(&t);

    var obuf: [4096]u8 = undefined;
    var fw = std.Io.File.stdout().writer(io, &obuf);
    const w = &fw.interface;

    try w.print("{{\n  \"orbits\": {d},\n  \"orbit_len_sum\": {d},\n  \"persistent_nop_residues\": [", .{ a.n_orbits, a.sum_orbit_len });
    var first = true;
    for (0..94) |r| if (a.persistent[r]) {
        try w.print("{s}{d}", .{ if (first) "" else ", ", r });
        first = false;
    };
    try w.print("],\n  \"ops\": {{\n", .{});
    for (OP_NAMES, 0..) |name, oi| {
        try w.print("    \"{s}\": [", .{name});
        first = true;
        for (0..94) |r| {
            const m = a.single[oi][r];
            if (m == 0) continue;
            const min_len: usize = @ctz(m);
            try w.print("{s}{{\"r\": {d}, \"min_orbit\": {d}, \"period2\": {}, \"run_before_strict\": {d}, \"run_after_strict\": {d}, \"run_before_lax\": {d}, \"run_after_lax\": {d}}}", .{
                if (first) "" else ", ",                 r,                        min_len,
                (m & (@as(u128, 1) << 2)) != 0,          runLen(&a, r, -1, false), runLen(&a, r, 1, false),
                runLen(&a, r, -1, true),                 runLen(&a, r, 1, true),
            });
            first = false;
        }
        try w.print("]{s}\n", .{if (oi + 1 < OP_NAMES.len) "," else ""});
    }
    var pairs: [MAXD][MAXD]bool = undefined;
    const strict = maxSites(&a, false, 0b111, &pairs);
    var n_pairs_strict: usize = 0;
    for (pairs) |row| for (row) |b| {
        if (b) n_pairs_strict += 1;
    };
    const lax = maxSites(&a, true, 0b111, &pairs);
    var per_op: [D_OPS][2]usize = undefined;
    for (0..D_OPS) |oi| {
        per_op[oi][0] = maxSites(&a, false, @as(u8, 1) << @intCast(oi), &pairs);
        per_op[oi][1] = maxSites(&a, true, @as(u8, 1) << @intCast(oi), &pairs);
    }
    try w.print("  }},\n  \"max_sites_per_shared_cell_strict\": {d},\n  \"delta_pairs_strict\": {d},\n  \"max_sites_per_shared_cell_lax\": {d},\n  \"max_sites_same_op\": {{", .{ strict, n_pairs_strict, lax });
    for (0..D_OPS) |oi| {
        try w.print("{s}\"{s}\": {{\"strict\": {d}, \"lax\": {d}}}", .{ if (oi == 0) "" else ", ", OP_NAMES[oi], per_op[oi][0], per_op[oi][1] });
    }
    try w.print("}}\n}}\n", .{});
    try w.flush();
}
