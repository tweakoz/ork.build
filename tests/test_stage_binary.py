"""Runtime prefix scanning across ELF/Mach-O layouts and real compiler output."""
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from obt.stage_binary import runtime_prefix_references

PREFIX = b'/fixture/source-stage'


def elf(wide=True, endian='<', runtime=True, extended=False):
    names = b'\0.shstrtab\0.rodata\0.dynstr\0.debug_info\0.interp\0'
    section_fmt = endian + ('IIQQQQIIQQ' if wide else 'IIIIIIIIII')
    entry_size = struct.calcsize(section_fmt)
    header_size = 64 if wide else 52
    count = 6
    data = bytearray(header_size + count * entry_size)
    sections = [(0, 0, 0, 0, 0, count if extended else 0,
                 1 if extended else 0, 0, 0, 0)]
    for name, kind, flags, content in (
            (b'.shstrtab', 3, 0, names),
            (b'.rodata', 1, 2, PREFIX if runtime else b'safe runtime data'),
            (b'.dynstr', 3, 2, PREFIX),
            (b'.debug_info', 1, 0, PREFIX),
            (b'.interp', 1, 2, PREFIX)):
        offset = len(data)
        data.extend(content + b'\0')
        sections.append((names.index(name), kind, flags, 0, offset, len(content) + 1, 0, 0, 1, 0))
    ident = b'\x7fELF' + bytes((2 if wide else 1, 1 if endian == '<' else 2, 1)) + b'\0' * 9
    data[:16] = ident
    header_fmt = endian + ('HHIQQQIHHHHHH' if wide else 'HHIIIIIHHHHHH')
    struct.pack_into(header_fmt, data, 16, 2, 62 if wide else 3, 1, 0, 0,
                     header_size, 0, header_size, 0, 0, entry_size,
                     0 if extended else count, 0xffff if extended else 1)
    for index, section in enumerate(sections):
        struct.pack_into(section_fmt, data, header_size + index * entry_size, *section)
    # Simulates old dynstr left in padding after a loader metadata rewrite.
    data.extend(b'abandoned:' + PREFIX)
    return bytes(data)


def macho(wide=True, endian='<', runtime=True, section_type=2, debug=False):
    header_fmt = endian + ('IiiIIIII' if wide else 'IiiIIII')
    segment_fmt = endian + ('II16sQQQQiiII' if wide else 'II16sIIIIiiII')
    section_fmt = endian + ('16s16sQQIIIIIIII' if wide else '16s16sIIIIIIIII')
    header_size = struct.calcsize(header_fmt)
    command_size = struct.calcsize(segment_fmt) + struct.calcsize(section_fmt)
    payload = PREFIX + b'\0' if runtime else b'safe\0'
    offset = header_size + command_size
    data = bytearray(offset + len(payload))
    header = (0xfeedfacf if wide else 0xfeedface, 0x1000007 if wide else 7, 3,
              2, 1, command_size, 0)
    struct.pack_into(header_fmt, data, 0, *(header + (0,) if wide else header))
    segment_name = b'__DWARF' if debug else b'__TEXT'
    struct.pack_into(segment_fmt, data, header_size, 0x19 if wide else 1,
                     command_size, segment_name, 0, len(data), 0, len(data), 7, 5, 1, 0)
    section = (b'__cstring', segment_name, offset, len(payload), offset, 0, 0, 0,
               section_type | (0x02000000 if debug else 0), 0, 0)
    struct.pack_into(section_fmt, data, header_size + struct.calcsize(segment_fmt),
                     *(section + (0,) if wide else section))
    data[offset:] = payload
    data.extend(b'ignored trailing metadata:' + PREFIX)
    return bytes(data)


def fat(images, wide=False, endian='>'):
    fmt = endian + ('iiQQII' if wide else 'iiIII')
    data = bytearray(8 + len(images) * struct.calcsize(fmt))
    struct.pack_into(endian + 'II', data, 0, 0xcafebabf if wide else 0xcafebabe, len(images))
    for index, image in enumerate(images):
        entry = (0x1000007, 3, len(data), len(image), 0)
        struct.pack_into(fmt, data, 8 + index * struct.calcsize(fmt), *(entry + (0,) if wide else entry))
        data.extend(image)
    return bytes(data)


class RuntimeBinaryTests(unittest.TestCase):
    def scan(self, data):
        with tempfile.TemporaryDirectory(prefix='obt-runtime-binary-') as tmp:
            path = Path(tmp) / 'fixture'
            path.write_bytes(data)
            return runtime_prefix_references(path, PREFIX)

    def test_elf_word_sizes_byte_orders_and_extended_numbering(self):
        for wide in (False, True):
            for endian in ('<', '>'):
                for extended in (False, True):
                    with self.subTest(wide=wide, endian=endian, extended=extended):
                        self.assertTrue(self.scan(elf(wide, endian, True, extended)))
                        self.assertFalse(self.scan(elf(wide, endian, False, extended)))

    def test_macho_word_sizes_byte_orders_and_metadata_exclusions(self):
        for wide in (False, True):
            for endian in ('<', '>'):
                with self.subTest(wide=wide, endian=endian):
                    self.assertTrue(self.scan(macho(wide, endian)))
                    self.assertTrue(self.scan(macho(wide, endian, section_type=0)))  # regular data
                    self.assertFalse(self.scan(macho(wide, endian, runtime=False)))
                    self.assertFalse(self.scan(macho(wide, endian, debug=True)))
                    for zero_fill in (1, 0xc, 0x12):
                        self.assertFalse(self.scan(macho(wide, endian, section_type=zero_fill)))

    def test_universal_scans_every_slice_including_later_architecture(self):
        for wide in (False, True):
            for endian in ('<', '>'):
                with self.subTest(wide=wide, endian=endian):
                    self.assertTrue(self.scan(fat([macho(runtime=False), macho(False, '>', True)], wide, endian)))
                    self.assertFalse(self.scan(fat([macho(runtime=False), macho(False, '>', False)], wide, endian)))

    def test_malformed_recognized_binaries_fail_closed(self):
        fixtures = [b'\x7fELF', b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe',
                    elf()[:80], macho()[:100], fat([macho()])[:50]]
        for image in fixtures:
            with self.subTest(length=len(image), magic=image[:4]):
                with self.assertRaises(ValueError):
                    self.scan(image)
        # A reference in slice one must not hide invalid later metadata.
        with self.assertRaises(ValueError):
            self.scan(fat([macho(), b'\xcf\xfa\xed\xfe']))
        with self.assertRaises(ValueError):
            self.scan(fat([b'unknown format']))

    def test_out_of_bounds_runtime_section_is_rejected(self):
        image = bytearray(elf())
        struct.pack_into('<Q', image, 64 + 2 * 64 + 24, 2**63)
        with self.assertRaises(ValueError):
            self.scan(image)
        image = bytearray(macho())
        struct.pack_into('<I', image, 32 + 72 + 48, 0xffffffff)
        with self.assertRaises(ValueError):
            self.scan(image)

    def test_generic_files_remain_callers_responsibility(self):
        self.assertIsNone(self.scan(b''))
        self.assertIsNone(self.scan(PREFIX))
        self.assertIsNone(self.scan(b'\0binary-data' + PREFIX))

    @unittest.skipUnless(shutil.which('cc'), 'requires native compiler')
    def test_real_native_compiled_runtime_string(self):
        with tempfile.TemporaryDirectory(prefix='obt-native-prefix-') as tmp:
            root = Path(tmp)
            source, binary = root / 'fixture.c', root / 'fixture'
            source.write_text('#include <stdio.h>\nint main(void) { return puts("' + PREFIX.decode() + '/settings"); }\n')
            subprocess.run(['cc', '-g', str(source), '-o', str(binary)], check=True)
            self.assertTrue(runtime_prefix_references(binary, PREFIX))
            source.write_text('int main(void) { return 0; }\n')
            subprocess.run(['cc', '-g', str(source), '-o', str(binary)], check=True)
            self.assertFalse(runtime_prefix_references(binary, PREFIX))


if __name__ == '__main__':
    unittest.main()
