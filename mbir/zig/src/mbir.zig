const std = @import("std");

pub const version: u8 = 0;

pub const Op = enum(u8) {
    halt = 0x00,
    push_const = 0x01,
    pop = 0x02,
    dup = 0x03,
    load_local = 0x04,
    store_local = 0x05,
    add = 0x06,
    sub = 0x07,
    mul = 0x08,
    cmp_eq = 0x09,
    cmp_lt = 0x0a,
    cmp_gt = 0x0b,
    jump = 0x0c,
    jump_if_false = 0x0d,
    call = 0x0e,
    return_ = 0x0f,
    out_byte = 0x10,
    in_byte = 0x11,
};

pub const DecodeError = error{ BadOpcode, BadOperand };
pub const RuntimeError = error{ BadOpcode, BadOperand, StackUnderflow, Unsupported };

pub const Instruction = struct {
    op: Op,
    operand_a: u8 = 0,
    operand_b: u8 = 0,
    operand_u24: u32 = 0,
    next_pc: usize,
};

fn operandWidth(op: Op) usize {
    return switch (op) {
        .push_const, .load_local, .store_local => 1,
        .jump, .jump_if_false => 3,
        .call => 2,
        else => 0,
    };
}

fn asOp(byte: u8) DecodeError!Op {
    return switch (byte) {
        0x00 => .halt,
        0x01 => .push_const,
        0x02 => .pop,
        0x03 => .dup,
        0x04 => .load_local,
        0x05 => .store_local,
        0x06 => .add,
        0x07 => .sub,
        0x08 => .mul,
        0x09 => .cmp_eq,
        0x0a => .cmp_lt,
        0x0b => .cmp_gt,
        0x0c => .jump,
        0x0d => .jump_if_false,
        0x0e => .call,
        0x0f => .return_,
        0x10 => .out_byte,
        0x11 => .in_byte,
        else => error.BadOpcode,
    };
}

pub fn decodeAt(code: []const u8, pc: usize) DecodeError!Instruction {
    if (pc >= code.len) return error.BadOperand;
    const op = try asOp(code[pc]);
    const width = operandWidth(op);
    if (pc + 1 + width > code.len) return error.BadOperand;

    var result = Instruction{ .op = op, .next_pc = pc + 1 + width };
    switch (op) {
        .push_const, .load_local, .store_local => result.operand_a = code[pc + 1],
        .jump, .jump_if_false => result.operand_u24 = @as(u32, code[pc + 1]) |
            (@as(u32, code[pc + 2]) << 8) |
            (@as(u32, code[pc + 3]) << 16),
        .call => {
            result.operand_a = code[pc + 1];
            result.operand_b = code[pc + 2];
        },
        else => {},
    }
    return result;
}

pub fn validate(code: []const u8) DecodeError!void {
    var pc: usize = 0;
    while (pc < code.len) {
        const instruction = try decodeAt(code, pc);
        pc = instruction.next_pc;
    }
}

pub const State = enum { running, halted, failed };

pub const Vm = struct {
    code: []const u8,
    pc: usize = 0,
    stack: [256]u8 = [_]u8{0} ** 256,
    sp: usize = 0,
    state: State = .running,

    pub fn init(code: []const u8) DecodeError!Vm {
        try validate(code);
        return .{ .code = code };
    }

    fn push(self: *Vm, value: u8) RuntimeError!void {
        if (self.sp == self.stack.len) return error.StackUnderflow;
        self.stack[self.sp] = value;
        self.sp += 1;
    }

    fn pop(self: *Vm) RuntimeError!u8 {
        if (self.sp == 0) return error.StackUnderflow;
        self.sp -= 1;
        return self.stack[self.sp];
    }

    pub fn step(self: *Vm) RuntimeError!void {
        if (self.state != .running) return;
        const instruction = decodeAt(self.code, self.pc) catch |err| return err;
        self.pc = instruction.next_pc;
        switch (instruction.op) {
            .halt => self.state = .halted,
            .push_const => try self.push(instruction.operand_a),
            .pop => _ = try self.pop(),
            .dup => {
                const value = try self.pop();
                try self.push(value);
                try self.push(value);
            },
            else => return error.Unsupported,
        }
    }

    pub fn run(self: *Vm) RuntimeError!void {
        while (self.state == .running) try self.step();
    }
};
