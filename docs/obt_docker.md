# OBT Docker Support

---

## Overview

OBT provides Docker module support for containerized development environments and services. Unlike the main OBT staging environment, Docker modules create isolated containers for specific workflows.

---

## Available Docker Modules

Based on the codebase scan, OBT includes several Docker modules:

- **sagemath**: Mathematical computing environment with Jupyter
- **androiddev**: Android development environment
- **ps1dev**: PlayStation 1 development tools
- **cicd**: Continuous integration/deployment support
- **ub-focal**: Ubuntu Focal base environment
- **realsense2**: Intel RealSense camera support

---

## Basic Usage

### List Docker Modules

```bash
obt.docker.list.py
```

### Build Docker Image

```bash
obt.docker.build.py <module_name>
```

### Launch Docker Container

```bash
obt.docker.launch.py <module_name>
```

### Kill Running Container

```bash
obt.docker.kill.py <container_name>
```

---

## Docker Module Structure

Docker modules are located in `modules/docker/` and typically contain:

```
modules/docker/mymodule/
├── mymodule.py
├── Dockerfile
└── entrypoint.sh
```

---

## CI/CD Docker Support

[Details needed about the CI/CD module implementation]

---

## Creating Custom Docker Modules

[Details needed about creating new Docker modules]

---

## Integration with OBT Environment

Docker modules can access the OBT staging directory and share dependencies with the host environment.

[More details needed about volume mounting and environment variable passing]

---

## Docker BuildX Support

```bash
obt.docker.install.buildx.py
```

[Details needed about BuildX usage]

---

## Troubleshooting

If you encounter build issues:

```bash
# Clean all Docker images
docker system prune --all
```

---

## Notes

- Docker modules are designed for development, not production deployment
- Requires Docker to be installed separately
- Consider using rootless Docker for security