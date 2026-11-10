"""Build the StickS3 offset-0 image without modifying any input header.

PlatformIO runs this after firmware.bin. It can also be run independently:
  python scripts/merge_sticks3.py --build-dir .pio/build/sticks3 \
    --framework-dir <PlatformIO framework-arduinoespressif32 directory>
"""
import argparse
import hashlib
import os
from pathlib import Path
import struct
import tempfile

FLASH_BYTES = 8 * 1024 * 1024


def check_image(data, name):
    """Validate ESP32-S3 identity, flash header, checksum, and image digest."""
    if len(data) < 24 or data[0] != 0xE9 or not 1 <= data[1] <= 16:
        raise ValueError(f"{name}: invalid ESP image header")
    if struct.unpack_from("<H", data, 12)[0] != 9:
        raise ValueError(f"{name}: expected ESP32-S3 chip ID 9")
    # Actual esp32-s3-devkitc-1 / qio_opi build headers are DIO, 80MHz, 8MB.
    # The bootloader subsequently configures quad flash. Never rewrite these
    # bytes after the appended image digest has been calculated.
    if data[2:4] != b"\x02\x3f":
        raise ValueError(f"{name}: expected DIO / 80MHz / 8MB image header")
    pos, checksum = 24, 0xEF
    for _ in range(data[1]):
        if pos + 8 > len(data):
            raise ValueError(f"{name}: truncated segment header")
        length = struct.unpack_from("<I", data, pos + 4)[0]
        pos += 8
        if pos + length > len(data):
            raise ValueError(f"{name}: truncated segment")
        for byte in data[pos:pos + length]:
            checksum ^= byte
        pos += length
    checksum_pos = pos + (15 - pos % 16)
    if checksum_pos >= len(data) or data[checksum_pos] != checksum:
        raise ValueError(f"{name}: invalid image checksum")
    if data[23] not in (0, 1):
        raise ValueError(f"{name}: invalid digest flag")
    if data[23] == 1:
        end = checksum_pos + 1
        if data[end:end + 32] != hashlib.sha256(data[:end]).digest():
            raise ValueError(f"{name}: invalid image SHA-256 digest")


def check_partitions(data, firmware_size):
    if not data or len(data) > 0x1000 or len(data) % 32:
        raise ValueError("partitions: invalid table size")
    regions, app_size, found_md5 = [], None, False
    expected = {(1, 2): (0x9000, 0x5000),  # NVS: board identity hint only.
                (1, 0): (0xE000, 0x2000),  # OTA metadata / boot_app0.
                (0, 0x10): (0x10000, 0x330000)}
    found = set()
    for pos in range(0, len(data), 32):
        entry = data[pos:pos + 32]
        if entry == b"\xff" * 32:
            break
        magic = struct.unpack_from("<H", entry)[0]
        if magic == 0xEBEB:
            if entry[16:] != hashlib.md5(data[:pos]).digest():
                raise ValueError("partitions: invalid table MD5")
            found_md5 = True
            break
        if magic != 0x50AA:
            raise ValueError("partitions: invalid entry magic")
        kind, subtype, offset, size = struct.unpack_from("<BBII", entry, 2)
        if (kind, subtype) == (1, 3):
            raise ValueError("partitions: flash core dumps are forbidden")
        key = (kind, subtype)
        if key in found or expected.get(key) != (offset, size):
            raise ValueError("partitions: unexpected partition or layout")
        found.add(key)
        if not size or offset < 0x9000 or offset + size > FLASH_BYTES:
            raise ValueError("partitions: entry outside 8MB flash layout")
        if any(offset < end and offset + size > start for start, end in regions):
            raise ValueError("partitions: overlapping entries")
        regions.append((offset, offset + size))
        if kind == 0 and subtype == 0x10 and offset == 0x10000:
            app_size = size
    if not found_md5 or found != set(expected) or app_size is None or firmware_size > app_size:
        raise ValueError("partitions: missing/invalid app0 or firmware too large")


def assemble(segments):
    """Merge non-overlapping segments and verify exact bytes plus erased gaps."""
    segments = sorted(segments, key=lambda item: item[0])
    end = 0
    for offset, data, name in segments:
        if offset < end or not data or offset + len(data) > FLASH_BYTES:
            raise ValueError(f"{name}: overlapping, empty, or out-of-flash segment")
        end = offset + len(data)
    merged = bytearray(b"\xff" * end)
    for offset, data, _ in segments:
        merged[offset:offset + len(data)] = data
    verify_merged(bytes(merged), segments)
    return bytes(merged)


def verify_merged(merged, segments):
    end = 0
    for offset, data, name in segments:
        if merged[offset:offset + len(data)] != data:
            raise ValueError(f"{name}: merged bytes differ from build input")
        if merged[end:offset] != b"\xff" * (offset - end):
            raise ValueError("merged image: non-erased gap")
        end = offset + len(data)
    if len(merged) != end:
        raise ValueError("merged image: incorrect length")


def merge_sticks3(build_dir, framework_dir, output):
    build_dir, framework_dir, output = map(Path, (build_dir, framework_dir, output))
    segments = [
        (0x0, (build_dir / "bootloader.bin").read_bytes(), "bootloader"),
        (0x8000, (build_dir / "partitions.bin").read_bytes(), "partitions"),
        (0xE000, (framework_dir / "tools/partitions/boot_app0.bin").read_bytes(), "boot_app0"),
        (0x10000, (build_dir / "firmware.bin").read_bytes(), "firmware"),
    ]
    check_image(segments[0][1], "bootloader")
    check_image(segments[3][1], "firmware")
    check_partitions(segments[1][1], len(segments[3][1]))
    if len(segments[2][1]) != 0x2000:
        raise ValueError("boot_app0: expected the framework's 8192-byte image")
    merged = assemble(segments)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(merged)
        verify_merged(temporary.read_bytes(), segments)
        os.replace(temporary, output)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    print(f"Verified StickS3 merged image: {output} ({len(merged)} bytes, offset 0x0)")
    return output


try:
    Import("env")  # PlatformIO / SCons supplies this function.
except NameError:
    env = None

if env is not None:
    def build_action(source, target, env):
        board = env.BoardConfig()
        if board.get("build.mcu") != "esp32s3" or board.get("upload.flash_size") != "8MB":
            raise ValueError("StickS3 merge requires ESP32-S3 with 8MB flash")
        if int(env.subst("$ESP32_APP_OFFSET"), 0) != 0x10000:
            raise ValueError("StickS3 merge requires application offset 0x10000")
        framework = env.PioPlatform().get_package_dir("framework-arduinoespressif32")
        merge_sticks3(env.subst("$BUILD_DIR"), framework,
                     Path(env.subst("$PROJECT_DIR")) / "dist/seeder-sticks3-merged.bin")

    env.AddPostAction("$BUILD_DIR/${PROGNAME}.bin", build_action)
elif __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", required=True)
    parser.add_argument("--framework-dir", required=True)
    parser.add_argument("--output", default="dist/seeder-sticks3-merged.bin")
    args = parser.parse_args()
    merge_sticks3(args.build_dir, args.framework_dir, args.output)
