## RTEMS 6.1 Release Notes

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

* TBD

#### API Additions

* `RTEMS_ALIGN_UP()`

* `RTEMS_ALIGN_DOWN()`

* `rtems_task_config`

* `rtems_task_construct()`

* `RTEMS_TASK_STORAGE_SIZE`

* `RTEMS_TASK_STORAGE_ALIGNMENT`

#### API Implementation Improvements

* TBD

#### API Deprecations

* `rtems_iterate_over_all_threads()`.  Use `rtems_task_iterate()` instead.

* `rtems_get_current_processor()`.  Use `rtems_scheduler_get_processor()` instead.

* `rtems_get_processor_count()`.  Use `rtems_scheduler_get_processor_maximum()` instead.

* `boolean` is deprecated.  Use `bool` instead.

* `single_precision` is deprecated.  Use `float` instead.

* `double_precision` is deprecated.  Use `double` instead.

* `proc_ptr` is deprecated.  Use a proper function pointer type.

* rtems_context

* rtems_context_fp

* rtems_extension

* `rtems_io_lookup_name()` is deprecated. Use `stat()` instead.

* region_information_block

* `rtems_thread_cpu_usage_t` is deprecated. Use `struct timespec` instead.

* `rtems_rate_monotonic_period_time_t` is deprecated. Use `struct timespec` instead.

* `_Copyright_Notice` is deprecated.  Use `rtems_get_copyright_notice()` instead.

* `_RTEMS_version` is deprecated.  Use `rtems_get_version_string()` instead.

* `RTEMS_MAXIMUM_NAME_LENGTH` is deprecated. Use `sizeof(rtems_name)` instead.

* `RTEMS_COMPILER_NO_RETURN_ATTRIBUTE` is deprecated. Use `RTEMS_NO_RETURN` instead.

* `RTEMS_COMPILER_PURE_ATTRIBUTE` is deprecated. Use `RTEMS_PURE` instead.

* `RTEMS_COMPILER_DEPRECATED_ATTRIBUTE` is deprecated. Use `RTEMS_DEPRECATED` instead.

* `RTEMS_COMPILER_UNUSED_ATTRIBUTE` is deprecated. Use `RTEMS_UNUSED` instead.

* `RTEMS_COMPILER_PACKED_ATTRIBUTE` is deprecated. Use `RTEMS_PACKED` instead.

* Including <rtems/system.h> is deprecated.  This header file will be removed in RTEMS 6.

#### API Removals

* TBD

### SMP Support Improvements

* TBD

### Configuration Changes

* TBD

* New configuration options:

    * `CONFIGURE_MAXIMUM_THREAD_LOCAL_STORAGE_SIZE`

    * `CONFIGURE_MINIMUM_TASKS_WITH_USER_PROVIDED_STORAGE`

* Renamed configuration options:

    * TBD

* Removed configuration options:

    * TBD

## RTEMS Shell Improvements

The following improvements were made to the RTEMS Shell:

* TBD

## General

* TBD

## Architectures

Removed obsolete architectures:

* Epiphany

* PowerPC SPE

Obsoleted architectures:

* TBD

## BSPs and Device Drivers

* General

    * TBD

* New BSPs

    * BSPs for ARCH

        * `BSP` - TBD

* Significant updates to existing BSPs

    * `ARCH/BSP`: TBD

* Removal of obsoleted BSPs

    * `ARCH/BSP`

    * `powerpc/brs5l`

    * `powerpc/brs6l`

    * `powerpc/dp2`

    * `powerpc/mpc5566evb_spe`

    * `powerpc/mpc5643l_dpu`

    * `powerpc/mpc5643l_evb`

    * `powerpc/mpc5674f_ecu508_app`

    * `powerpc/mpc5674f_ecu508_boot`

    * `powerpc/mpc5674fevb_spe`

    * `powerpc/mpc5674f_rsm6`

* Obsoleted BSPs

    * `m68k/gen68302`

    * `m68k/ods68302`

    * `powerpc/mbx8xx`

* Drivers

    * TBD

## Newlib Changes

* TBD

## Ecosystem

* TBD
