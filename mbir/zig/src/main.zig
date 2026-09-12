const std = @import("std");
const mbir = @import("mbir");

pub fn main(init: std.process.Init) !void {
    _ = init;
    // M1 smoke executable. External bytecode/input transport is M3.
    var vm = try mbir.Vm.init(&[_]u8{0x00});
    try vm.run();
}
