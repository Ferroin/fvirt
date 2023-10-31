# fvirt Domain Test Images

This directory contains kernel and initramfs images used by the fvirt test suite for testing live domains.

The kernel and initramfs are custom-made using [buildroot](https://buildroot.org/) specifically for this purpose. The
kernel itself is built using a highly minimal config without loadable module or most security features, including
just the drivers that are actually needed by our test environment. The initramfs consists of Busybox, acpid on
systems that need it to respond to shutdown signals, the QEMU guest agent, and a small handful of specific tools
for verifying particular virtual hardware setups. The initramfs boots using busybox init, starts acpid, and then
spawns a shell on the main console.

The kernel and initramfs were specifically crafted to fulfill two particular goals:

- Boot and shut down as quickly as possible. The x86\_64 images take about 2.5 seconds from starting the domain
  to providing a usable shell prompt on my Ryzen 9 3950X test system (multiple seconds faster than almost any other
  distro), and only need about 2 seconds to shut down on the same system. This helps keep test runs as quick as possible.
- Use as little memory as possible at runtime. All the images boot reliably with as little as 96 MiB of RAM.

The actual kernel and initramfs images are stored using git-lfs, so you need that to be able to make use of them.

Each subdirectory corresponds to a specific CPU architecture, and should contain the following files:

- `kernel.img`: The kernel image.
- `initramfs.img`: The initramfs image.
- `buildroot-commit`: Contains the commit hash of the version of Buildroot used to build the kernel and initramfs.
- `buildroot-config`: Contains the Buildroot configuration used to build the kernel and initramfs.
- `kernel-config`: Contains the kernel configuration used to build the kernel.
- `busybox-config`: Contains the Busybox configuration used to build the copy of busybox included in the initramfs.
