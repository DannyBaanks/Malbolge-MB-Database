//! G5b-2 P1: planificador de disposición (una variable, dos llamadores, retorno por bandera).
//!
//! Uso: plan <positive|control_a|control_b>
//! Imprime JSON: celdas de código (en la imagen) y objetivos de datos (por encima
//! de la imagen, los escribe el preámbulo BolgeForge). Solo aritmética numérica
//! (op = (w + pc) mod 94); el ensamblador valida contra xlat1 del vendor.
//!
//! Isla de tick para op en X: [X op de fase][X+1 JMP]. Entrando con salto a X-1
//! y d = T: X lee T+1 (si lee d), X+1 lee T+2 (= X, rearma X por aterrizaje)
//! y luego T+3 (siguiente destino - 1); se sigue con d = T+4? No:
//! - JMP de entrada lee mem[T], incrementa d -> T+1, aterriza en X.
//! - X (op) se ejecuta con d = T+1 (lee mem[T+1] si es d-op), d -> T+2.
//! - X+1 (JMP) se ejecuta con d = T+2: lee mem[T+2] (= X), cifra X (rearme),
//!   aterriza en X+1, d -> T+3.
//! - X+1 (JMP) se ejecuta con d = T+3: lee mem[T+3] (= next - 1), d -> T+4.
//! Bandera F (pc≡60, w=74) y reloj K (pc≡2, w=66): sin tick (JMP lee T+2 directo).
const std = @import("std");

const OP_JMP: i64 = 4;
const OP_OUT: i64 = 5;
const OP_ROT: i64 = 39;
const OP_MOVD: i64 = 40;
const OP_NOP: i64 = 68;

const BLOCK_START: i64 = 15000;
const V0: i64 = 12345;
const V: i64 = 41000;
const P1: i64 = 42000;
const S_LOOP: i64 = 45000;
const HANDOFF: i64 = 56000;

const Mode = enum {
    positive,
    control_a,
    control_b,
};

fn encode(q: i64, pc: i64) i64 {
    return 33 + @mod(q - pc - 33, 94);
}

/// Palabra de fase 70/74 que decodifica op en pc (la otra fase es NOP efectivo).
fn phaseWord(pc: i64, op: i64) ?i64 {
    const words = [_]i64{ 74, 70 };
    for (words) |w| {
        if (@mod(w + pc, 94) == op) return w;
    }
    return null;
}

fn nextResidue(start: i64, rem: i64) i64 {
    var pc = start;
    while (@mod(pc, 94) != rem) : (pc += 1) {}
    return pc;
}

fn nextPhase(start: i64, op: i64) struct { pc: i64, word: i64 } {
    var pc = start;
    while (true) : (pc += 1) {
        if (phaseWord(pc, op)) |w| return .{ .pc = pc, .word = w };
    }
}

const Entry = struct {
    addr: i64,
    val: i64,
};

const Plan = struct {
    mode: Mode,
    k: i64,
    f: i64,
    movd_v: i64,
    rot_v: i64,
    out_op: i64,
    movd_loop: i64,
    code_buf: [12]Entry = undefined,
    code_len: usize = 0,
    target_buf: [32]Entry = undefined,
    target_len: usize = 0,

    fn putCode(self: *Plan, addr: i64, val: i64) void {
        self.code_buf[self.code_len] = .{ .addr = addr, .val = val };
        self.code_len += 1;
    }

    fn putTarget(self: *Plan, addr: i64, val: i64) void {
        for (self.target_buf[0..self.target_len]) |*e| {
            if (e.addr == addr) {
                e.val = val;
                return;
            }
        }
        self.target_buf[self.target_len] = .{ .addr = addr, .val = val };
        self.target_len += 1;
    }
};

fn buildPlan(mode: Mode) Plan {
    var p: i64 = BLOCK_START;
    const k_pc = nextResidue(p, 2);
    p = k_pc + 2;
    const f_pc = nextResidue(p, 60);
    p = f_pc + 2;
    const movd_v = nextPhase(p, OP_MOVD);
    p = movd_v.pc + 2;
    const rot_v = nextPhase(p, OP_ROT);
    p = rot_v.pc + 2;
    const out_op = nextPhase(p, OP_OUT);
    p = out_op.pc + 2;
    const movd_loop = nextPhase(p, OP_MOVD);

    var plan: Plan = .{
        .mode = mode,
        .k = k_pc,
        .f = f_pc,
        .movd_v = movd_v.pc,
        .rot_v = rot_v.pc,
        .out_op = out_op.pc,
        .movd_loop = movd_loop.pc,
    };

    // Islas de código: [op][JMP]
    plan.putCode(k_pc, 66);
    plan.putCode(k_pc + 1, encode(OP_JMP, k_pc + 1));

    plan.putCode(f_pc, 74);
    plan.putCode(f_pc + 1, encode(OP_JMP, f_pc + 1));

    plan.putCode(movd_v.pc, movd_v.word);
    plan.putCode(movd_v.pc + 1, encode(OP_JMP, movd_v.pc + 1));

    plan.putCode(rot_v.pc, rot_v.word);
    plan.putCode(rot_v.pc + 1, encode(OP_JMP, rot_v.pc + 1));

    plan.putCode(out_op.pc, out_op.word);
    plan.putCode(out_op.pc + 1, encode(OP_JMP, out_op.pc + 1));

    plan.putCode(movd_loop.pc, movd_loop.word);
    plan.putCode(movd_loop.pc + 1, encode(OP_JMP, movd_loop.pc + 1));

    // Handoff desde el preámbulo hacia MOVD_loop para iniciar en K con d = S_LOOP + 1
    plan.putTarget(HANDOFF, movd_loop.pc - 1);
    plan.putTarget(HANDOFF + 1, S_LOOP - 2);

    // Variable V y llamada compartida a ROT_V
    plan.putTarget(V - 2, movd_v.pc);
    plan.putTarget(V - 1, rot_v.pc - 1);
    plan.putTarget(V, V0);
    plan.putTarget(V + 1, rot_v.pc);
    plan.putTarget(V + 2, f_pc - 1);
    plan.putTarget(V + 3, P1);

    // Continuación de A (desde V+4 cuando F estaba en NOP)
    plan.putTarget(V + 4, out_op.pc - 1);
    plan.putTarget(V + 6, out_op.pc);
    plan.putTarget(V + 7, out_op.pc - 1);
    plan.putTarget(V + 9, out_op.pc);
    plan.putTarget(V + 10, movd_v.pc - 1);
    plan.putTarget(V + 11, V - 3);

    // Continuación de B (desde P1+1 cuando F estaba armada)
    if (mode == .control_b) {
        plan.putTarget(P1 + 1, out_op.pc - 1);
        plan.putTarget(P1 + 3, out_op.pc);
        plan.putTarget(P1 + 4, movd_loop.pc - 1);
        plan.putTarget(P1 + 5, S_LOOP - 2);
    } else {
        plan.putTarget(P1 + 1, f_pc - 1);
        plan.putTarget(P1 + 3, out_op.pc - 1);
        plan.putTarget(P1 + 5, out_op.pc);
        plan.putTarget(P1 + 6, movd_loop.pc - 1);
        plan.putTarget(P1 + 7, S_LOOP - 2);
    }

    // Retorno de iteración: K -> (conmutar F) -> A -> B -> loop
    plan.putTarget(S_LOOP - 1, movd_loop.pc);
    plan.putTarget(S_LOOP, k_pc - 1);
    if (mode == .control_a) {
        plan.putTarget(S_LOOP + 2, movd_v.pc - 1);
        plan.putTarget(S_LOOP + 3, V - 3);
    } else {
        plan.putTarget(S_LOOP + 2, f_pc - 1);
        plan.putTarget(S_LOOP + 3, S_LOOP + 3);
        plan.putTarget(S_LOOP + 4, movd_v.pc - 1);
        plan.putTarget(S_LOOP + 5, V - 3);
    }

    return plan;
}

fn parseMode(arg: []const u8) ?Mode {
    if (std.mem.eql(u8, arg, "positive")) return .positive;
    if (std.mem.eql(u8, arg, "control_a")) return .control_a;
    if (std.mem.eql(u8, arg, "control_b")) return .control_b;
    return null;
}

pub fn main(init: std.process.Init) !void {
    const io = init.io;
    const arena = init.arena.allocator();
    const args = try init.minimal.args.toSlice(arena);
    if (args.len != 2) {
        std.log.err("uso: {s} <positive|control_a|control_b>", .{args[0]});
        std.process.exit(2);
    }
    const mode = parseMode(args[1]) orelse {
        std.log.err("modo desconocido: {s}", .{args[1]});
        std.process.exit(2);
    };

    const plan = buildPlan(mode);

    var obuf: [4096]u8 = undefined;
    var fw = std.Io.File.stdout().writer(io, &obuf);
    const w = &fw.interface;

    try w.print("{{\n  \"mode\": \"{s}\",\n  \"v0\": {d},\n  \"handoff\": {d},\n", .{
        @tagName(plan.mode), V0, HANDOFF,
    });
    try w.print("  \"data\": {{\"V\": {d}, \"p1\": {d}, \"s_loop\": {d}}},\n", .{ V, P1, S_LOOP });
    try w.print(
        "  \"islands\": {{\"K\": {d}, \"F\": {d}, \"MOVD_V\": {d}, \"ROT_V\": {d}, \"OUT\": {d}, \"MOVD_LOOP\": {d}}},\n",
        .{ plan.k, plan.f, plan.movd_v, plan.rot_v, plan.out_op, plan.movd_loop },
    );

    try w.writeAll("  \"code\": {");
    for (plan.code_buf[0..plan.code_len], 0..) |e, idx| {
        try w.print("{s}\"{d}\": {d}", .{ if (idx == 0) "" else ", ", e.addr, e.val });
    }
    try w.writeAll("},\n  \"targets\": {");
    for (plan.target_buf[0..plan.target_len], 0..) |e, idx| {
        try w.print("{s}\"{d}\": {d}", .{ if (idx == 0) "" else ", ", e.addr, e.val });
    }
    try w.writeAll("}\n}\n");
    try w.flush();
}
