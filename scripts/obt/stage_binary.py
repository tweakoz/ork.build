"""Read-only runtime data inspection for staging relocation.

Loader paths are validated separately by the caller. Section-based scanning
avoids treating debug strings and abandoned copies of loader metadata as live
runtime references. A recognized binary with unusable metadata raises ValueError;
None means the file is not a supported binary format.
"""
import mmap
import os
import struct


class _Image:
    def __init__(self, data, base=0, size=None):
        self.data = data
        self.base = base
        self.size = len(data) - base if size is None else size

    def bounds(self, offset, size):
        if offset < 0 or size < 0 or offset > self.size or size > self.size - offset:
            raise ValueError("binary metadata points outside its image")

    def unpack(self, fmt, offset):
        self.bounds(offset, struct.calcsize(fmt))
        return struct.unpack_from(fmt, self.data, self.base + offset)

    def bytes(self, offset, size):
        self.bounds(offset, size)
        return self.data[self.base + offset:self.base + offset + size]

    def contains(self, offset, size, needle):
        self.bounds(offset, size)
        return self.data.find(needle, self.base + offset, self.base + offset + size) >= 0

    def cstring(self, offset, limit):
        self.bounds(offset, limit)
        end = self.data.find(b"\0", self.base + offset, self.base + offset + limit)
        if end < 0:
            raise ValueError("unterminated binary section name")
        if end - self.base - offset > 4096:
            raise ValueError("unsupported oversized binary section name")
        return self.data[self.base + offset:end]


def _elf(image, needle):
    ident = image.bytes(0, 16)
    if ident[4] not in (1, 2) or ident[5] not in (1, 2) or ident[6] != 1:
        raise ValueError("unsupported ELF class, byte order, or version")
    endian = "<" if ident[5] == 1 else ">"
    wide = ident[4] == 2
    header = image.unpack(endian + ("HHIQQQIHHHHHH" if wide else "HHIIIIIHHHHHH"), 16)
    if header[2] != 1:
        raise ValueError("unsupported ELF version")
    section_offset, header_size = header[5], header[7]
    entry_size, count, names_index = header[10:13]
    fmt = endian + ("IIQQQQIIQQ" if wide else "IIIIIIIIII")
    minimum = struct.calcsize(fmt)
    if header_size < (64 if wide else 52) or not section_offset or entry_size < minimum:
        raise ValueError("ELF section metadata is unavailable or malformed")

    def section(index):
        return image.unpack(fmt, section_offset + index * entry_size)

    zero = section(0)
    if count == 0:
        count = zero[5]  # ELF extended section numbering
    if names_index == 0xffff:
        names_index = zero[6]
    if not count or names_index >= count:
        raise ValueError("invalid ELF section count or name-table index")
    image.bounds(section_offset, entry_size * count)
    names = section(names_index)
    if names[1] != 3:
        raise ValueError("ELF section names are unavailable")
    image.bounds(names[4], names[5])
    found = False
    for index in range(1, count):
        name_index, kind, flags, _addr, offset, size, *_ = section(index)
        if name_index >= names[5]:
            raise ValueError("invalid ELF section name offset")
        name = image.cstring(names[4] + name_index, names[5] - name_index)
        if kind != 8:  # SHT_NOBITS has memory size but no file bytes
            image.bounds(offset, size)
        # Only mapped data/code. Loader string tables and dynamic entries have
        # their own semantic validation; .interp is validated there as well.
        if not flags & 2 or kind in (0, 2, 3, 6, 8, 11) or name == b".interp":
            continue
        if name.startswith((b".debug", b".zdebug")):
            continue
        found = image.contains(offset, size, needle) or found
    return found


_THIN = {b"\xce\xfa\xed\xfe": ("<", False), b"\xcf\xfa\xed\xfe": ("<", True),
         b"\xfe\xed\xfa\xce": (">", False), b"\xfe\xed\xfa\xcf": (">", True)}
_FAT = {b"\xca\xfe\xba\xbe": (">", False), b"\xbe\xba\xfe\xca": ("<", False),
        b"\xca\xfe\xba\xbf": (">", True), b"\xbf\xba\xfe\xca": ("<", True)}


def _macho(image, needle):
    endian, wide = _THIN[image.bytes(0, 4)]
    fmt = endian + ("IiiIIIII" if wide else "IiiIIII")
    header = image.unpack(fmt, 0)
    count, command_bytes = header[4:6]
    cursor = struct.calcsize(fmt)
    image.bounds(cursor, command_bytes)
    end = cursor + command_bytes
    if count > command_bytes // 8:
        raise ValueError("invalid Mach-O load command count")
    found = False
    for _ in range(count):
        command, size = image.unpack(endian + "II", cursor)
        if size < 8 or size % (8 if wide else 4) or cursor + size > end:
            raise ValueError("invalid Mach-O load command size")
        if command in (1, 0x19):  # LC_SEGMENT / LC_SEGMENT_64
            segment_wide = command == 0x19
            if segment_wide != wide:
                raise ValueError("Mach-O segment width disagrees with header")
            segment_fmt = endian + ("II16sQQQQiiII" if wide else "II16sIIIIiiII")
            section_fmt = endian + ("16s16sQQIIIIIIII" if wide else "16s16sIIIIIIIII")
            segment_size = struct.calcsize(segment_fmt)
            section_size = struct.calcsize(section_fmt)
            if size < segment_size:
                raise ValueError("truncated Mach-O segment")
            segment = image.unpack(segment_fmt, cursor)
            segment_name = segment[2].split(b"\0", 1)[0]
            file_offset, file_size, sections = segment[5], segment[6], segment[9]
            image.bounds(file_offset, file_size)
            if segment_size + sections * section_size > size:
                raise ValueError("truncated Mach-O section table")
            for index in range(sections):
                section = image.unpack(section_fmt, cursor + segment_size + index * section_size)
                section_segment = section[1].split(b"\0", 1)[0]
                section_bytes, offset, flags = section[3], section[4], section[8]
                if segment_name and section_segment != segment_name:
                    raise ValueError("Mach-O section belongs to a different segment")
                if flags & 0xff in (1, 0xc, 0x12):  # zero-fill, giant zero-fill, TLS zero-fill
                    continue
                image.bounds(offset, section_bytes)
                if section_bytes and (offset < file_offset or offset + section_bytes > file_offset + file_size):
                    raise ValueError("Mach-O section lies outside its file-backed segment")
                if segment_name in (b"__DWARF", b"__LINKEDIT") or flags & 0x02000000:
                    continue
                found = image.contains(offset, section_bytes, needle) or found
        cursor += size
    if cursor != end:
        raise ValueError("Mach-O load command sizes disagree with header")
    return found


def _binary(image, needle):
    magic = image.bytes(0, min(4, image.size))
    if magic == b"\x7fELF":
        return _elf(image, needle)
    if magic in _THIN:
        return _macho(image, needle)
    if magic in _FAT:
        endian, wide = _FAT[magic]
        count = image.unpack(endian + "I", 4)[0]
        fmt = endian + ("iiQQII" if wide else "iiIII")
        entry_size = struct.calcsize(fmt)
        if not count:
            raise ValueError("empty universal Mach-O image")
        image.bounds(8, count * entry_size)
        found = False
        for index in range(count):
            entry = image.unpack(fmt, 8 + index * entry_size)
            offset, size = entry[2:4]
            image.bounds(offset, size)
            if offset < 8 + count * entry_size or size < 4:
                raise ValueError("invalid universal Mach-O slice")
            child = _Image(image.data, image.base + offset, size)
            if child.bytes(0, 4) not in _THIN:
                raise ValueError("unsupported universal Mach-O slice format")
            found = _macho(child, needle) or found
        return found
    return None


def runtime_prefix_references(path, prefix):
    """Return bool for ELF/Mach-O, None for other files; malformed binaries raise.

    Only file-backed runtime sections are scanned. The caller must separately
    verify ELF dynamic paths/interpreter and Mach-O loader commands.
    """
    needle = os.fsencode(prefix)
    if not needle:
        raise ValueError("empty source prefix")
    with open(path, "rb") as stream:
        if os.fstat(stream.fileno()).st_size == 0:
            return None
        with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
            return _binary(_Image(data), needle)
