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
pub const RuntimeError = error{
    BadOpcode,
    BadOperand,
    BadTarget,
    BadSlot,
    StackUnderflow,
    NoFrame,
    MaxSteps,
    Unsupported,
};

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
    locals: [256]u8 = [_]u8{0} ** 256,
    local_set: [256]bool = [_]bool{false} ** 256,
    frames: [64]Frame = undefined,
    frame_count: usize = 0,
    input: []const u8 = &[_]u8{},
    input_cursor: usize = 0,
    output: [4096]u8 = [_]u8{0} ** 4096,
    output_len: usize = 0,
    steps: usize = 0,
    max_steps: usize = 1_000_000,
    state: State = .running,

    const Frame = struct {
        return_pc: usize,
        locals: [256]u8,
        local_set: [256]bool,
    };

    pub fn init(code: []const u8) DecodeError!Vm {
        try validate(code);
        return .{ .code = code };
    }

    pub fn initWithInput(code: []const u8, input: []const u8) DecodeError!Vm {
        var vm = try init(code);
        vm.input = input;
        return vm;
    }

    pub fn setMaxSteps(self: *Vm, limit: usize) void {
        self.max_steps = limit;
    }

    pub fn outputBytes(self: *const Vm) []const u8 {
        return self.output[0..self.output_len];
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

    fn isBoundary(self: *const Vm, target: usize) bool {
        var pc: usize = 0;
        while (pc < self.code.len) {
            if (pc == target) return true;
            const instruction = decodeAt(self.code, pc) catch return false;
            pc = instruction.next_pc;
        }
        return false;
    }

    fn stepInner(self: *Vm) RuntimeError!void {
        if (self.state != .running) return;
        const instruction = decodeAt(self.code, self.pc) catch |err| return err;
        self.steps += 1;
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
            .load_local => {
                if (!self.local_set[instruction.operand_a]) return error.BadSlot;
                try self.push(self.locals[instruction.operand_a]);
            },
            .store_local => {
                self.locals[instruction.operand_a] = try self.pop();
                self.local_set[instruction.operand_a] = true;
            },
            .add, .sub, .mul, .cmp_eq, .cmp_lt, .cmp_gt => {
                const b = try self.pop();
                const a = try self.pop();
                const value: u8 = switch (instruction.op) {
                    .add => a +% b,
                    .sub => a -% b,
                    .mul => a *% b,
                    .cmp_eq => if (a == b) 1 else 0,
                    .cmp_lt => if (a < b) 1 else 0,
                    .cmp_gt => if (a > b) 1 else 0,
                    else => unreachable,
                };
                try self.push(value);
            },
            .jump => {
                const target = instruction.operand_u24;
                if (!self.isBoundary(target)) return error.BadTarget;
                self.pc = target;
            },
            .jump_if_false => {
                const cond = try self.pop();
                const target = instruction.operand_u24;
                if (!self.isBoundary(target)) return error.BadTarget;
                if (cond == 0) self.pc = target;
            },
            .call => {
                const target = instruction.operand_a;
                const nargs = instruction.operand_b;
                if (!self.isBoundary(target) or self.frame_count == self.frames.len) return error.BadTarget;
                if (self.sp < nargs) return error.StackUnderflow;
                const frame = Frame{
                    .return_pc = self.pc,
                    .locals = self.locals,
                    .local_set = self.local_set,
                };
                self.frames[self.frame_count] = frame;
                self.frame_count += 1;
                self.locals = [_]u8{0} ** 256;
                self.local_set = [_]bool{false} ** 256;
                var i: usize = 0;
                while (i < nargs) : (i += 1) {
                    self.locals[nargs - 1 - i] = try self.pop();
                    self.local_set[nargs - 1 - i] = true;
                }
                self.pc = target;
            },
            .return_ => {
                if (self.frame_count == 0) return error.NoFrame;
                self.frame_count -= 1;
                const frame = self.frames[self.frame_count];
                self.pc = frame.return_pc;
                self.locals = frame.locals;
                self.local_set = frame.local_set;
            },
            .out_byte => {
                if (self.output_len == self.output.len) return error.BadOperand;
                self.output[self.output_len] = try self.pop();
                self.output_len += 1;
            },
            .in_byte => {
                const value: u8 = if (self.input_cursor < self.input.len) blk: {
                    const v = self.input[self.input_cursor];
                    self.input_cursor += 1;
                    break :blk v;
                } else 0xff;
                try self.push(value);
            },
        }
    }

    pub fn step(self: *Vm) RuntimeError!void {
        self.stepInner() catch |err| {
            self.state = .failed;
            return err;
        };
    }

    pub fn run(self: *Vm) RuntimeError!void {
        while (self.state == .running) {
            if (self.steps >= self.max_steps) return error.MaxSteps;
            try self.step();
        }
    }
};
