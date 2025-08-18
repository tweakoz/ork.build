# OBT FPGA/Vivado Support

---

## Overview

OBT includes support for FPGA development workflows, including integration with Xilinx Vivado and other FPGA toolchains.

---

## Supported Tools

Based on the dependency scan:

### Synthesis Tools
- **yosys**: Open-source synthesis tool
- **nextpnr**: Place-and-route tool
- **icestorm**: Tools for Lattice iCE40 FPGAs
- **arachnepnr**: Place-and-route for iCE40

### Xilinx Vivado
- Located in `/opt/Xilinx/` (user-installed)
- [Integration details needed]

### Soft CPU Cores
- **lm32**: LatticeMico32 soft processor
- **rv32**: RISC-V 32-bit toolchain
- **zephyr**: RTOS support

### HDL Frameworks
- **litex**: Python-based SoC builder
- [Additional framework details needed]

---

## Building FPGA Dependencies

```bash
# Build yosys synthesis tool
obt.dep.build.py yosys

# Build nextpnr place-and-route
obt.dep.build.py nextpnr

# Build icestorm tools
obt.dep.build.py icestorm

# Build LiteX
obt.dep.build.py litex
```

---

## Toolchain Setup

### RISC-V Toolchain

```bash
# Build RISC-V binutils
obt.dep.build.py rv32_binutils

# Build RISC-V GCC
obt.dep.build.py rv32_gcc
```

### LatticeMico32 Toolchain

```bash
obt.dep.build.py lm32_binutils
obt.dep.build.py lm32_gcc
```

---

## Vivado Integration

[Details needed about:]
- How OBT detects Vivado installation
- Environment variable setup
- License management
- Project integration

---

## LiteX SoC Development

[Details needed about:]
- LiteX module structure
- SoC generation workflow
- Integration with soft cores

---

## Example FPGA Project Structure

[Example project structure needed]

---

## FPGA-Specific Environment Variables

[List of FPGA-related environment variables that OBT sets]

---

## Hardware Testing Support

The codebase includes LinuxCNC support, suggesting hardware control capabilities:

```bash
obt.dep.build.py linuxcnc
```

[Details about hardware testing integration needed]

---

## Simulation Support

- **simavr**: AVR microcontroller simulator
[Additional simulation tool details needed]

---

## Notes

- FPGA tools require significant disk space
- Some tools may require specific Linux distributions
- Vivado must be installed separately in `/opt/`
- License servers may need configuration