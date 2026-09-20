# Contributing to Duster

Thanks for contributing to Duster! 🎉

Duster uses a simple, community-editable package registry. Adding a package mainly means preparing the installer archive, publishing it in the repository's `RELEASES/` directory, and adding a matching entry to `reg.sleep`.

## Package Requirements

Before contributing a package:

- The original `.exe` or `.msi` installer must be **25 MB or smaller**.
- The installer should be renamed to exactly one of:
  - `setup.exe`
  - `setup.msi`
- The archive must use **ZIP + Deflate + Normal** compression.
- The SHA256 value recorded in `reg.sleep` must match the **ZIP file** you upload to `RELEASES/`.
- The `file_name` in `reg.sleep` must exactly match the ZIP filename in `RELEASES/`.

## Step 1: Download the Installer

Download the official installer for the application you want to add.

The installer must be a `.exe` or `.msi` file and must be within Duster's **25 MB package limit**.

For example:

```text
SomeApp-0.1.exe
```

## Step 2: Rename the Installer

Rename the installer inside the archive to:

```text
setup.exe
```

or, for an MSI installer:

```text
setup.msi
```

Do not use a vendor-specific filename inside the archive. Duster expects the standard `setup.exe` / `setup.msi` name for installer types that use it.

## Step 3: Create the ZIP Archive

Use **7-Zip** to create the archive.

Create a normal ZIP archive with:

- Format: `zip`
- Compression method: `Deflate`
- Compression level: `Normal`

The resulting archive should contain the installer, for example:

```text
MyApp-0.1.zip
└── setup.exe
```

or:

```text
MyApp-0.1.zip
└── setup.msi
```

Keep the archive structure simple. The installer should be directly inside the ZIP unless the package specifically requires another layout.

## Step 4: Calculate the SHA256

Calculate the SHA256 hash of the **ZIP archive** you just created.

For example, if your archive is:

```text
MyApp-0.1.zip
```

calculate the SHA256 of `MyApp-0.1.zip`.

Copy the complete hash exactly as shown. You will put this value into `verification_hash` in `reg.sleep`.

## Step 5: Fork the Repository

Fork the Duster repository on GitHub.

Clone your fork locally and make your changes there.

## Step 6: Add the ZIP to `RELEASES/`

Place your ZIP archive in the repository's:

```text
RELEASES/
```

directory.

For example:

```text
RELEASES/MyApp-0.1.zip
```

The filename must be unique and must exactly match the `file_name` field you add to `reg.sleep`.

## Step 7: Add the Package to `reg.sleep`

Add a `package` entry to `reg.sleep` using this format:

```sleep
package
  name <name>
  license <simple license such as OpenSource, Noncommercial, Proprietary>
  version "<version, for example 0.1>"
  installer_type <Inno, NSIS, MSI, InstallShield, or Exe>
  verification_hash <SHA256 hash of the ZIP>
  category coll [<searchable terms separated by spaces>]
  file_name "<exact ZIP name in RELEASES/>"
```

### Example

```sleep
package
  name Greenshot
  license OpenSource
  version "1.3.315"
  installer_type Inno
  verification_hash 1e32db754aa99a2eeb219442ac8c65d604544eee5152ed912de14bcac6283cdc
  category coll [Screenshots Greenshot Image]
  file_name "Greenshot-1.3.315.zip"
```

### Field Guide

`name`

The application's name as users will search for it.

`license`

Use a simple description such as:

```text
OpenSource
Noncommercial
Proprietary
```

Use the license category that best describes the software. Do not invent a more specific license name unless it is useful for the package entry.

`version`

The application's version, stored as a string.

```sleep
version "1.2.3"
```

`installer_type`

Use the installer family that matches the package:

```text
Inno
NSIS
MSI
InstallShield
Exe
```

Try to use `Inno`, `NSIS`, `MSI`, or `InstallShield` when you know the installer type. `Exe` is the generic fallback and should be avoided when a known installer type can be used.

For `Exe`, Duster does **not** guess silent-install flags. It runs the executable normally. Do not rely on invented arguments such as `/S`, `/silent`, or `/quiet` unless the installer type explicitly supports them.

`verification_hash`

The SHA256 hash of the ZIP file uploaded to `RELEASES/`.

It must match the archive exactly.

`category`

A `coll` of searchable terms that help users find the package.

For example:

```sleep
category coll [Graphics Screenshots Image]
```

Use useful search terms such as the application's purpose, category, and common name.

`file_name`

The exact ZIP filename in `RELEASES/`.

These two must match exactly:

```text
RELEASES/MyApp-0.1.zip
```

```sleep
file_name "MyApp-0.1.zip"
```

## Step 8: Check Everything Before Opening a Pull Request

Before submitting your contribution, verify all of the following:

- The original installer is 25 MB or smaller.
- The installer inside the archive is named `setup.exe` or `setup.msi`.
- The archive is a ZIP using Deflate compression at Normal level.
- The ZIP is inside `RELEASES/`.
- The SHA256 in `reg.sleep` is the SHA256 of that exact ZIP.
- `file_name` exactly matches the ZIP filename.
- The version in `reg.sleep` matches the software being distributed.
- The installer type is correct.
- Search terms in `category` are useful.
- The package can be installed successfully with Duster.

## Step 9: Commit and Open a Pull Request

Commit your changes and push them to your fork.

Your pull request should include:

1. The new ZIP file in `RELEASES/`.
2. The matching package entry in `reg.sleep`.

Keep package contributions focused. Do not modify unrelated Duster code unless your contribution actually requires it.

## Installer Types

Duster supports several installer families:

| Installer Type | Use When |
|---|---|
| `Inno` | The installer is an Inno Setup installer |
| `NSIS` | The installer is an NSIS installer |
| `MSI` | The package is distributed as an MSI |
| `InstallShield` | The installer uses InstallShield |
| `Exe` | Generic executable fallback when no supported installer family applies |

Prefer a known installer type over `Exe` whenever possible.

## Important Notes

### Do Not Guess Installer Arguments

Duster should not invent command-line switches for an arbitrary executable. Different installers use different arguments.

For example, do not assume that every `.exe` supports:

```text
/S
/silent
/quiet
```

The generic `Exe` type is intentionally a **normal, non-silent fallback**.

### Administrator Privileges

Some installers require Administrator privileges.

Duster does not try to bypass Windows security or automatically invent an elevation workflow. When Windows reports that elevation is required, run Duster from an elevated Windows Terminal, PowerShell, or Command Prompt.

### Keep Packages Reproducible

The registry entry and release archive must describe the same package. A mismatched filename or SHA256 hash will prevent Duster from verifying the download correctly.

## Contribution Philosophy

Duster is community-driven:

> Anyone can search. Anyone can install. Anyone can modify the registry. Anyone can contribute packages.

Keep contributions simple, readable, and verifiable.
