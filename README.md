# virshx - A lightweight wrapper around libvirt to complement virsh

virshx is a minimalistic CLI wrapper around libvirt that is intended to
complement the existing `virsh` wrapper by providing useful functionality
that would normally need a nontrivial amount of scripting to achieve.

It can:

- Operate on domains in bulk by matching on names or arbitrary domain
  configuration. For example, virshx can shut down all domains whose
  name matches a specific regex, or pause all domains in a specific
  security context.
- Wait for domain shutdown to complete when shutting down domains.
- Apply XSL transformations to various libvirt XML objects.

virshx also includes a much more Python-friendly wrapper for libvirt
than the existing libvirt-python bindings, including things like proper
context manager support for connections and property access for many
common parts of domain configuration.

## Why virshx?

There exist a number of useful frontends for libvirt, but pretty much
none of them have good support for bulk modification of domains. The
existing virsh frontend can technically do this for some simple changes,
but it requires scripting to do it, and it only supports relatively
simple changes. The only real way currently to perform complex bulk
modifications to domain configuration is to shut down libvirtd and then
directly edit the domain config files.

Additionally, scripting is often required to do theoretically simple
things like shutting down or pausing a group of domains.

virshx exists to solve these two specific problems. It provides a robust
syntax for matching domains (or most other libvirt objects) based on a
combination of XPath (to specify what part of the domain config to match
on) and Python regular expressions (to specify what, exactly, to match),
together with a mechanism for running operations on the matched
domains. It also allows use of XSLT documents to edit domain configuration
(or other objects), allowing complex changes to domains to be made
quickly and (relatively) easily without needing to shut down libvirtd.

## Dependencies

virshx is written in Python 3, and requires Python 3.11 or newer.

It additionally requires the following Python packages beyond what is
found in the Python standard library:

- libvirt-python 9.6 or newer
- lxml 4.9 or newer
