# virshx - A lightweight wrapper around libvirt to complement virsh

virshx is a minimalistic CLI wrapper around libvirt that is intended to
complement the existing `virsh` wrapper by providing useful functionality
that would normally need a nontrivial amount of scripting to achieve.

It also includes enhanced Python bindings for the libvirt API that wrap
the low-level official bindings in a more Pythonic manner, making it
nicer to work with libvirt from Python.

## What does it do?

### virshx CLI

The virshx CLI tool can:

- List libvirt objects in much greater detail than virsh, with
  configurable columns. For example, when listing domains, it can
  include everything that `virsh list` does, as well as extra info like
  the generation ID, the OS type, the CPU architecture, and the domain
  ‘title’.
- Use a custom timeout to wait for domains to shut down. This cleanly
  encapsulates a relatively common use case which requires scripting to
  work with virsh, allowing for much simpler scripts.
- Modify libvirt object XML using XSLT documents. This allows complex
  programmatic editing of domain configuration without needing complex
  scripting to extract the XML, process it, and then feed it back in to
  libvirt to redefine the object.
- Modify a handful of commonly used properties of libvirt objects directly
  without having to deal with XSLT. Just want to change the machine type
  for a given domain? virshx can do that in one command.
- Match objects to operate on using XPath expressions and Python
  regexes. Special options are provided to simplify matching on commonly
  used properties, such as domain architecture or storage pool type. This
  matching works with almost all other commands provided by virshx,
  allowing you to easily operate on groups of objects in bulk.

### virshx.libvirt

The libvirt bindings included with virshx provide a number of enhancements
over the official bindings, including:

- Hypervisor connections support the context manager protocol.
- Hypervisor objects provide iterator and mapping access to objects like
  domains and storage pools, including automatic connection management.
- Storage pools provide iterator and mapping access to their volumes.
- Domain states are an enumerable (like they are in the C API) instead
  of just being an opaque number (like they are in libvirt-python).
- Object XML is directly accessible as lxml Element objects.
- Things that should logically return an empty sequence when nothing
  is matched usually do so, in contrast to libvirt-python often returning
  None instead.
- libvirt URIs are objects that can be easily modified to change things
  like the driver or host.
- Most common properties of objects are accessible using regular attribute
  access instead of requiring either method calls or manual lookup in the
  object’s XML config. This includes writability for many of these
  properties.

## What doesn’t it do?

Because virshx is intended to complement the existing virsh tool, not
replace it, we very intentionally only provide commands that actually
extend functionality provided by virsh. With some very limited exceptions,
we simply don’t have commands that directly replicate virsh behavior
in a 1:1 manner.

Currently, virshx and virshx.libvirt also do not support working with
most libvirt objects other than domains, storage pools, and volumes. This
is because that functionality is what I specifically needed for my own
usage, thus it was the first thing I implemented. I plan to expand this
further to at least include netowrks and network interfaces, but it’s
not a priority at the moment.

Both of these may change in the future.

## Dependencies

virshx is written in Python 3, and requires Python 3.11 or newer.

It additionally requires the following Python packages beyond what is
found in the Python standard library:

- blessed 1.20 or newer
- Click 8.1 or newer
- frozendict 2.3 or newer
- libvirt-python 9.6 or newer
- lxml 4.9 or newer

## Why not just contribute to libvirt/virsh?

For one, I’m not a C developer, and I recognize that it would have
taken me far longer to add much of this functionality to virsh than it
took me to implement it as a Python CLI tool.

Secondarily, I’m not confident that a number of things that virshx
does would have actually been accepted into virsh, especially the XPath
and XSLT related bits. virsh was always intended primarily as an example
application and testing tool, not a primary user interface for libvirt,
and that limits what they end up including.
