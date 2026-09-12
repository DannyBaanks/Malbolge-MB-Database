const std = @import("std");
const mbir = @import("mbir");

const MAX_FILE_BYTES: u64 = 1024 * 1024;

const CliResult = struct {
    status: []const u8,
    error_name: ?[]const u8,
    steps: usize,
    output: []const u8,
};

fn reasonFor(err: anyerror) []const u8 {
    return switch (err) {
        error.BadOpcode => "BAD_OPCODE",
        error.BadOperand => "BAD_OPERAND",
        error.BadTarget => "BAD_TARGET",
        error.BadSlot => "BAD_SLOT",
        error.StackUnderflow => "STACK_UNDERFLOW",
        error.NoFrame => "NO_FRAME",
        error.MaxSteps => "MAX_STEPS",
        error.Unsupported => "UNSUPPORTED",
        else => @errorName(err),
    };
}

fn runCode(code: []const u8, input: []const u8, max_steps: usize) CliResult {
    var vm = mbir.Vm.init(code) catch |err| {
        return .{ .status = "ERROR", .error_name = reasonFor(err), .steps = 0, .output = "" };
    };
    vm.input = input;
    vm.setMaxSteps(max_steps);
    vm.run() catch |err| {
        return .{
            .status = if (err == error.MaxSteps) "MAX_STEPS" else "ERROR",
            .error_name = if (err == error.MaxSteps) null else reasonFor(err),
            .steps = vm.steps,
            .output = vm.outputBytes(),
        };
    };
    return .{
        .status = "HALTED",
        .error_name = null,
        .steps = vm.steps,
        .output = vm.outputBytes(),
    };
}

fn printResult(io: std.Io, result: CliResult) !void {
    var stdout_buffer: [8192]u8 = undefined;
    var stdout_writer = std.Io.File.stdout().writer(io, &stdout_buffer);
    const stdout = &stdout_writer.interface;
    try stdout.print(
        "{{\"schema\":\"mbir-zig-result/1\",\"status\":\"{s}\",\"error\":",
        .{result.status},
    );
    if (result.error_name) |name| {
        try stdout.print("\"{s}\"", .{name});
    } else {
        try stdout.writeAll("null");
    }
    try stdout.print(",\"steps\":{d},\"output\":[", .{result.steps});
    for (result.output, 0..) |byte, index| {
        if (index != 0) try stdout.writeAll(",");
        try stdout.print("{d}", .{byte});
    }
    try stdout.writeAll("]}\n");
    try stdout.flush();
}

pub fn main(init: std.process.Init) !void {
    const allocator = init.gpa;
    const args = try init.minimal.args.toSlice(allocator);
    if (args.len < 2 or args.len > 5) {
        var stderr_buffer: [512]u8 = undefined;
        var stderr_writer = std.Io.File.stderr().writer(init.io, &stderr_buffer);
        const stderr = &stderr_writer.interface;
        try stderr.writeAll("usage: mbir-zig <program.mbir> [input.bin] [--max-steps N]\n");
        try stderr.flush();
        std.process.exit(2);
    }

    var input_path: ?[]const u8 = null;
    var max_steps: usize = 1_000_000;
    var index: usize = 2;
    while (index < args.len) {
        if (std.mem.eql(u8, args[index], "--max-steps")) {
            if (index + 1 >= args.len) return error.MissingMaxSteps;
            max_steps = try std.fmt.parseInt(usize, args[index + 1], 10);
            index += 2;
        } else if (input_path == null) {
            input_path = args[index];
            index += 1;
        } else {
            return error.ExtraArgument;
        }
    }

    const cwd = std.Io.Dir.cwd();
    const code = try cwd.readFileAlloc(init.io, args[1], allocator, .limited(MAX_FILE_BYTES));
    const input = if (input_path) |path|
        try cwd.readFileAlloc(init.io, path, allocator, .limited(MAX_FILE_BYTES))
    else
        "";

    const result = runCode(code, input, max_steps);
    try printResult(init.io, result);
    std.process.exit(if (result.error_name == null) 0 else 1);
}
