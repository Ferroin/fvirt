# fvirt Public API

fvirt uses Semantic Versioning, as outlined in the [Semantic Versioning
v2.0.0 specification](https://semver.org/spec/v2.0.0.html).

The following aspects of the `fvirt` CLI tool are considered part of
the fvirt’s public API:

1. The name and intended functionality of all CLI commands which have
   not been explicitly hidden or deprecated.
2. The names and intended functionality of any options for the commands
   covered by item 1.
3. The order and purpose of any non-option arguments for the commands
   covered by item 1.
4. The default formatting of logging output on stderr.

The following components of the `fvirt` Python package are additionally
considered part of fvirt’s public API:

1. The behavior and public methods and properties of the `VersionNumber`
   class located in the `fvirt.version` module.
2. The presence of a constant named `VERSION` available at the top
   level of the `fvirt` package, with a value indicating the version
   number of the installed version of `fvirt` expressed as an instance of
   `fvirt.version.VersionNumber`.
3. The presence of a constant named `API_VERSION` available in
   `fvirt.libvirt` with a value indicating the version number of the
   underlying `python-libvirt` bindings being used by fvirt, expressed as
   an instance of `fvirt.version.VersionNumber`.
4. The general behavior and public methods and properties of the
   classes that would be imported by `from fvirt.libvirt import *`.
5. The presence, purpose, and types as indicated by type annotations,
   of the constants that would be imported by `from fvirt.libvirt
   import *`.
6. The structure and typing of the Pydantic models located in
   `fvirt.libvirt.models`.

A few specific exceptions to this exist in a number of places in the
code. They will always be explicitly called out in the docstring of the
affected module, class, or function.

Anything not explicitly included above is _NOT_ considered part of
fvirt’s public API, and users should not rely on it.

The public API as present in release v0.1.0 is largely consistent with
the expected public API for v1.0.0, and thus is not expected to change in
significant, backwards incompatible, ways prior to the release of v1.0.0.
