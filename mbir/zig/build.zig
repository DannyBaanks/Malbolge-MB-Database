const std = @import("std");

pub fn build(b: *std.Build) !void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const module = b.createModule(.{
        .root_source_file = b.path("src/mbir.zig"),
        .target = target,
        .optimize = optimize,
    });

    const exe = b.addExecutable(.{
        .name = "mbir-zig",
        .root_module = b.createModule(.{
            .root_source_file = b.path("src/main.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });
    exe.root_module.addImport("mbir", module);
    b.installArtifact(exe);

    const tests = b.addTest(.{
        .root_module = b.createModule(.{
            .root_source_file = b.path("tests/runtime.zig"),
            .target = target,
            .optimize = optimize,
        }),
    });
    tests.root_module.addImport("mbir", module);
    const run_tests = b.addRunArtifact(tests);
    const test_step = b.step("test", "Run MBIR Zig tests");
    test_step.dependOn(&run_tests.step);
}
