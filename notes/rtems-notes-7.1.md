## RTEMS 7.1 Release Notes

### RTEMS Improvements

In this section, we discuss public API level changes as well as improvements to
the implementation of those API routines.

Public API changes usually fall into one of the following categories:

* Addition of new methods

* Modifications to prototypes

* Deletion of obsoleted methods

Implementation improvements usually fall into one of the following categories:

* Algorithm improvements in execution time or memory usage

* Critical section reduction

### API Changes

* The value returned by `rtems_task_get_priority()` is 0 for tasks that are
  scheduled with deadlines using the EDF, CBS, and EDF SMP schedulers.

#### API Additions

* TBD

#### API Implementation Improvements

* TBD

#### API Deprecations

* TBD

#### API Removals

* `set_vector()` was removed. Use `rtems_interrupt_handler_install()` instead.
* TBD

### Configuration Changes

* Configuration changes:
    * The EDF, CBS, and EDF SMP schedulers now use the
      `CONFIGURE_MAXIMUM_PRIORITY` option to determine the valid priority
      range. Previously the range was fixed as `[0, INT_MAX]`. The default is
      now `[0, PRIORITY_DEFAULT_MAXIMUM]` consistent with other schedulers,
      where `PRIORITY_DEFAULT_MAXIMUM` typically is 255.

* New configuration options:

    * TBD

* Renamed configuration options:

    * TBD

* Removed configuration options:

    * TBD

### Source Builder

All build sets depending on github.com, git.rtems.org, and devel.rtems.org have
been migrated to use the appropriate resources on gitlab.rtems.org.

## RTEMS Shell Improvements

The following improvements were made to the RTEMS Shell:

* TBD

## General

* The obsolete libmisc/serdbg was removed. Use libdebugger instead. This functionality
  was not built as part of the 5 release series in anticipation of its removal.

* Add setup instructions for [NixOS](https://nixos.org/) to users guide.

## Architectures

Removed obsoleted architectures:

* Blackfin (bfin)
* Lattice Mico 32 (lm32)
* SPARC64
* SuperH (sh)
* V850

Obsoleted architectures:

* NIOS2
* aarch64 ilp32 variant

## BSPs and Device Drivers

* General

    * TBD

* New Architectures

    * TBD

* New BSPs

    * `arm/efm32gg11`
    * `aarch64/rk3399`
    * `aarch64/raspberry5`
    * `aarch64/xen`
    * `arm/efm32gg11`
    * `arm/stm32f446ze`
    * `arm/nucleo-h753zi`
    * `arm/stm32u5-grisp-nano`
    * `arm/xilinx-versal-rpu`

* Significant updates to existing BSPs

    * `ARCH/BSP`: TBD

* Removal of obsoleted BSPs

    * `bfin/TLL6527M`
    * `bfin/bf537Stamp`
    * `bfin/eZKit533`
    * `lm32/lm32_evr`
    * `lm32/lm32_evr_gdbsim`
    * `lm32/milkymist`
    * `m68k/gen68302`
    * `m68k/csb360`
    * `m68k/gen68340`
    * `m68k/gen68360`
    * `m68k/gen68360_040`
    * `m68k/pgh360`
    * `m68k/mcf5206elite`
    * `m68k/mcf52235`
    * `m68k/mcf5225x`
    * `m68k/mrm332`
    * `m68k/mvme147`
    * `m68k/mvme147s`
    * `m68k/mvme162`
    * `m68k/mvme162lx`
    * `m68k/mvme167`
    * `m68k/ods68302`
    * `powerpc/mvme5500 (use beatnik)`
    * `sparc64/niagara`
    * `sparc64/usiii`
    * `sh/gensh1`
    * `sh/gensh2`
    * `sh/gensh4`
    * `sh/simsh1`
    * `sh/simsh2`
    * `sh/simsh2e`
    * `sh/simsh4`
    * `v850/v850e1sim`
    * `v850/v850e2sim`
    * `v850/v850e2v3sim`
    * `v850/v850esim`
    * `v850/v850essim`
    * `v850/v850sim`

* Obsoleted BSPs

    * `powerpc/virtex`

* Drivers

    * TBD

## Newlib Changes

* TBD

## Ecosystem

* TBD

## Debugger Improvements 

* TBD
