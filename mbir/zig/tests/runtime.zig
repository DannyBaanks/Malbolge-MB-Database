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
