const std = @import("std");
const mbir = @import("mbir");

test "decoder accepts all MBIR v0 opcodes" {
    const code = [_]u8{
        0x00, 0x01, 0x7f, 0x02, 0x03, 0x04, 0x01, 0x05, 0x01,
        0x06, 0x07, 0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x00, 0x00, 0x00,
        0x0d, 0x00, 0x00, 0x00, 0x0e, 0x01, 0x00, 0x0f, 0x10, 0x11,
    };
    try mbir.validate(&code);
}

test "decoder reads u8 and u24 operands" {
    const push = try mbir.decodeAt(&[_]u8{ 0x01, 0xaa }, 0);
    try std.testing.expectEqual(@as(u8, 0xaa), push.operand_a);
    const jump = try mbir.decodeAt(&[_]u8{ 0x0c, 0x78, 0x56, 0x34 }, 0);
    try std.testing.expectEqual(@as(u32, 0x345678), jump.operand_u24);
}

test "decoder rejects unknown and truncated bytecode" {
    try std.testing.expectError(error.BadOpcode, mbir.validate(&[_]u8{0xff}));
    try std.testing.expectError(error.BadOperand, mbir.validate(&[_]u8{0x01}));
    try std.testing.expectError(error.BadOperand, mbir.validate(&[_]u8{0x0c, 0, 0}));
}

test "M1 stack executes halt push pop and dup" {
    var vm = try mbir.Vm.init(&[_]u8{ 0x01, 0x2a, 0x03, 0x02, 0x00 });
    try vm.run();
    try std.testing.expectEqual(mbir.State.halted, vm.state);
    try std.testing.expectEqual(@as(usize, 1), vm.sp);
    try std.testing.expectEqual(@as(u8, 0x2a), vm.stack[0]);
}

test "M1 reports stack underflow" {
    var vm = try mbir.Vm.init(&[_]u8{0x02});
    try std.testing.expectError(error.StackUnderflow, vm.run());
}

test "M2 executes modular arithmetic and locals" {
    var vm = try mbir.Vm.init(&[_]u8{
        0x01, 200, 0x01, 100, 0x06, // 200 + 100 = 44
        0x05, 0x03, 0x04, 0x03, 0x01, 2, 0x08, 0x00,
    });
    try vm.run();
    try std.testing.expectEqual(@as(u8, 88), vm.stack[0]);
}

test "M2 executes call and return with ordered arguments" {
    var vm = try mbir.Vm.init(&[_]u8{
        0x01, 2, 0x01, 3, 0x0e, 8, 2, // call function at 8 with (2, 3)
        0x00, 0x04, 0, 0x04, 1, 0x06, 0x0f,
    });
    try vm.run();
    try std.testing.expectEqual(@as(u8, 5), vm.stack[0]);
}

test "M2 executes input and output" {
    var vm = try mbir.Vm.initWithInput(&[_]u8{0x11, 0x10, 0x00}, "Z");
    try vm.run();
    try std.testing.expectEqualSlices(u8, "Z", vm.outputBytes());
}

test "M2 rejects invalid targets and enforces max steps" {
    var bad = try mbir.Vm.init(&[_]u8{ 0x0c, 1, 0, 0 });
    try std.testing.expectError(error.BadTarget, bad.run());

    var loop = try mbir.Vm.init(&[_]u8{ 0x0c, 0, 0, 0 });
    loop.setMaxSteps(3);
    try std.testing.expectError(error.MaxSteps, loop.run());
}
