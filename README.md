# ulvdm - The micro libvirt domain manager

ulvdm is a minimalistic CLI wrapper around libvirt that is intended to
complement the existing `virsh` wrapper by providing useful functionality
that would normally need a nontrivial amount of scripting to achieve.

It can:

- Generate domains based on Jinja2 templates, including support for
  querying external sources to populate network configuration.
- Perform simple transformations of domains using either XSLT or a
  simplified `jq`-like syntax.
- Operate on domains in bulk by matching on names or ulvdm metadata
  values. For example, ulvdm can shut down all domains whose name matches
  a specific regex.

## Dependencies

ulvdm is written in Python 3, and requires Python 3.11 or newer.

It additionally requires the following Python packages beyond what is
found in the Python standard library:

- libvirt-python 9.6 or newer
- Jinja2 3.1 or newer
