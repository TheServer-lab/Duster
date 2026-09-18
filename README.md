# Duster

**Duster** is an extremely lightweight, open-source software distribution CLI for Windows.

No giant package database. No complicated server infrastructure. No account required just to search for software.

**Anyone can search. Anyone can install. Anyone can modify the registry. Anyone can contribute packages.**

Duster is designed to keep software distribution simple, transparent, and community-driven.

## Features

* **Extremely lightweight** — Duster is a small CLI focused on doing one job.
* **Search packages** from the public registry.
* **Install software** directly from registry entries.
* **Upgrade installed software** when a newer registry version is available.
* **Uninstall software** through Windows' own uninstall registry.
* **SHA256 verification** for downloaded packages.
* **Community-editable registry** — anyone can submit changes or add packages.
* **GitHub-based distribution** — package artifacts can be hosted through GitHub releases.
* **No central server required** — the registry and package files can live on ordinary public repositories.
* **Multiple installer types** such as Inno, NSIS, MSI, InstallShield, and generic executable installers.

## The Idea

Duster is built around a simple model:

```text
Registry
   ↓
Find package
   ↓
Download artifact
   ↓
Verify SHA256
   ↓
Extract if necessary
   ↓
Run installer
```

The registry tells Duster what the package is and how it should be installed.

There is no hidden magic database deciding what software is allowed to exist.

## Searching

Anyone can search the registry:

```text
duster search greenshot
```

Duster searches package names and categories.

Example:

```text
Search results for 'greenshot':
  - Greenshot (1.3.315) [License: OpenSource]
    Category: Screenshots, Greenshot
```

## Installing

Install a package by its registry name:

```text
duster install greenshot
```

Duster downloads the configured artifact, verifies its SHA256 hash, extracts it when required, and runs the appropriate installer.

## Upgrading

Check the registry for a newer version:

```text
duster upgrade greenshot
```

Duster compares the installed version with the registry version and only performs an upgrade when the registry contains a newer version.

## Uninstalling

Uninstall software using:

```text
duster uninstall greenshot
```

Duster searches the normal Windows uninstall registry locations and prefers a package's `QuietUninstallString` when one is available.

## Listing Installed Software

```text
duster list
```

Example:

```text
greenshot 1.3.315
7zip 26.03
```

## Registry

Duster packages are described using a simple **SLEEP** registry format.

Example:

```sleep
package
  name Greenshot
  license OpenSource
  version "1.3.315"
  installer_type Inno
  verification_hash SHA256
  category coll [Screenshots Greenshot]
  file_name "Greenshot-INSTALLER-1.3.315-RELEASE.zip"
```

The registry contains the information Duster needs to locate, verify, and install a package.

### Installer Types

Duster supports installer families explicitly rather than blindly guessing command-line arguments.

For example:

```text
Inno
NSIS
MSI
InstallShield
Exe
```

`Exe` is the generic fallback for executable installers that do **not** have a known silent-install convention.

Duster does not randomly append `/S`, `/quiet`, or other flags to generic executables.

## Package Contributions

Duster is intentionally community-driven.

Anyone can contribute a new package or update an existing one by modifying the registry.

A package contribution can contain:

* Package name
* Version
* Installer type
* Download filename
* SHA256 verification hash
* Categories
* Other registry metadata required by Duster

The goal is to make adding software straightforward without requiring a complicated submission platform.

## Package Size

Duster's distribution model uses GitHub-hosted artifacts, so packages intended for the registry are limited to **25 MB per uploaded package artifact** under the project's distribution policy.

This keeps Duster focused on relatively small desktop utilities and avoids turning the registry into a general-purpose file hosting service.

Large software distributions are better handled by their own official download systems.

## Open Source

Duster is open source.

The registry is also designed to be openly inspectable and community-maintained.

That means users can see:

* What package is being installed
* Which version is being installed
* Where the artifact comes from
* Which SHA256 hash is expected
* Which installer type Duster will use

There is no need to blindly trust a mysterious binary database.

## Community Model

Duster follows a simple principle:

> **Anyone can search. Anyone can install. Anyone can modify the registry. Anyone can contribute packages.**

The registry is intended to be a shared community resource rather than a locked-down catalogue controlled by a single administrator.

That also means contributors are responsible for making sure package information is accurate and that submitted software comes from legitimate sources.

## Why Duster?

Modern package managers can become surprisingly complicated.

Duster takes a different approach:

**Keep the client tiny.
Keep the registry readable.
Keep the package format simple.
Keep the distribution open.**

Duster is not trying to become an operating system.

It is a small command-line tool for getting Windows software onto a machine without turning software distribution into a giant ecosystem of unnecessary machinery.

## Example

A typical workflow looks like this:

```text
duster search 7zip

duster install 7zip

duster list

duster upgrade 7zip

duster uninstall 7zip
```

That's it.

## Administrator Privileges

Some Windows installers require Administrator privileges.

Duster does not attempt to automatically elevate itself or bypass Windows' normal security model.

If an installer reports that elevation is required, open **Windows Terminal, PowerShell, or Command Prompt as Administrator** and run Duster again:

```text
duster install <package>
```

This is intentional. Duster handles software distribution; Windows handles authorization and elevation.


**Search. Install. Upgrade. Uninstall.**

## License

Duster is open source. See the repository's license file for the complete licensing terms.
