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

* If the processor set is not large enough to contain the processor set of
  the scheduler, then `rtems_scheduler_get_processor_set()` returns
  `RTEMS_INVALID_SIZE` instead of `RTEMS_INVALID_NUMBER`.

* If the processor set is not large enough to contain the processor
  affinity set of the task, then `rtems_task_get_affinity()` returns
  `RTEMS_INVALID_SIZE` instead of `RTEMS_INVALID_NUMBER`.

* If time-of-day argument is `NULL`, then `rtems_timer_fire_when()`,
  `rtems_timer_server_fire_when(), and `rtems_task_wake_when()` return
  `RTEMS_INVALID_ADDRESS` instead of `RTEMS_INVALID_CLOCK`.

* The time-of-day arguments in `rtems_timer_fire_when()`,
  `rtems_timer_server_fire_when(), and `rtems_task_wake_when()` were
  constified.

* If the entry point is `NULL`, then `rtems_task_start()` returns now
  `RTEMS_INVALID_ADDRESS`.

* If `rtems_task_delete()` is called from within interrupt context, then it
  returns now `RTEMS_CALLED_FROM_ISR`.

* The rate monotonic period statistics are no longer affected by
  `rtems_cpu_usage_reset()`.

* Termios
  * `txTaskCharsDequeued` has been added to `struct rtems_termios_tty`. With
    that the size of the structure changed. Libraries and applications that use
    the structure should be recompiled.
  * The `l_start` line discipline function now receives the number of characters
    that have been sent. It is save to ignore the extra parameter for
    applications that don't need it.

* The system termination procedure was simplified and the CPU port provided
  fatal halt handler was removed. See the section *23.2.2. System Termination
  Procedure* in the *RTEMS Classic API Guide*.

* The fatal extensions are now invoked with maskable interrupts disabled.

* The signature of the BSP reset function changed to
  `RTEMS_NO_RETURN void bsp_reset(rtems_fatal_source source, rtems_fatal_code code)`.
  This allows BSPs to pass the reset cause to a monitor or save it for the next
  boot sequence.

#### API Additions

* `RTEMS_ALIGN_UP()`

* `RTEMS_ALIGN_DOWN()`

* `rtems_get_build_label()`

* `rtems_get_target_hash()`

* `rtems_interrupt_clear()`

* `rtems_interrupt_entry_initialize()`

* `RTEMS_INTERRUPT_ENTRY_INITIALIZER()`

* `rtems_interrupt_entry_install()`

* `rtems_interrupt_entry_remove()`

* `rtems_interrupt_get_affinity()`

* `rtems_interrupt_get_attributes()`

* `rtems_interrupt_handler_install()`

* `rtems_interrupt_handler_iterate()`

* `rtems_interrupt_handler_remove()`

* `rtems_interrupt_is_pending()`

* `rtems_interrupt_raise()`

* `rtems_interrupt_raise_on()`

* `rtems_interrupt_server_action_prepend()`

* `rtems_interrupt_server_create()`

* `rtems_interrupt_server_delete()`

* `rtems_interrupt_server_entry_destroy()`

* `rtems_interrupt_server_entry_initialize()`

* `rtems_interrupt_server_entry_move()`

* `rtems_interrupt_server_entry_submit()`

* `rtems_interrupt_server_handler_install()`

* `rtems_interrupt_server_handler_iterate()`

* `rtems_interrupt_server_handler_remove()`

* `rtems_interrupt_server_initialize()`

* `rtems_interrupt_server_move()`

* `rtems_interrupt_server_request_destroy()`

* `rtems_interrupt_server_request_initialize()`

* `rtems_interrupt_server_request_set_vector()`

* `rtems_interrupt_server_request_submit()`

* `rtems_interrupt_server_resume()`

* `rtems_interrupt_server_set_affinity()`

* `rtems_interrupt_server_suspend()`

* `rtems_interrupt_set_affinity()`

* `rtems_interrupt_vector_disable()`

* `rtems_interrupt_vector_enable()`

* `rtems_interrupt_vector_is_enabled()`

* `RTEMS_MESSAGE_QUEUE_BUFFER()`

* `rtems_message_queue_construct()`

* `RTEMS_PARTITION_ALIGNMENT`

* `rtems_task_construct()`

* `RTEMS_TASK_STORAGE_SIZE()`

* `RTEMS_TASK_STORAGE_ALIGNMENT`

#### API Implementation Improvements

* The Classic API signal processing was reworked to avoid possible infinite
  recursions.  It is still strongly recommended to use the `RTEMS_NO_ASR` task
  mode for the signal handler.

* Zero size allocation results are now consistent accross directives, for
  example `malloc( 0 )` and `posix_memalign( &p, align, 0 )` return now a
  unique pointer (or `NULL` if the heap is empty).  In POSIX, zero size memory
  allocations are implementation-defined behaviour.  The implementation has two
  options:

  * https://pubs.opengroup.org/onlinepubs/9699919799/functions/malloc.html

  * https://pubs.opengroup.org/onlinepubs/9699919799/functions/posix_memalign.html

  Linux and FreeBSD return a unique pointer for zero size memory allocations.
  This approach is now also used in RTEMS as well throughout the memory
  allocation directives

#### API Deprecations

* `rtems_iterate_over_all_threads()`.  Use `rtems_task_iterate()` instead.

* `_Copyright_Notice` is deprecated.  Use `rtems_get_copyright_notice()` instead.

* `_RTEMS_version` is deprecated.  Use `rtems_get_version_string()` instead.

* `RTEMS_COMPILER_NO_RETURN_ATTRIBUTE` is deprecated. Use `RTEMS_NO_RETURN` instead.

* `RTEMS_COMPILER_PURE_ATTRIBUTE` is deprecated. Use `RTEMS_PURE` instead.

* `RTEMS_COMPILER_DEPRECATED_ATTRIBUTE` is deprecated. Use `RTEMS_DEPRECATED` instead.

* `RTEMS_COMPILER_UNUSED_ATTRIBUTE` is deprecated. Use `RTEMS_UNUSED` instead.

* `RTEMS_COMPILER_PACKED_ATTRIBUTE` is deprecated. Use `RTEMS_PACKED` instead.

#### API Removals

* The obsoleted header file <rtems/system.h> was removed.

* The never implemented `rtems_interrupt_cause()` directive was removed.

* Support for the RTEMS thread model used by GCC versions prior to 6.1 was
  removed (for example `rtems_gxx_once()`).

* The obsoleted `rtems_get_current_processor()` directive was removed.  Use
  `rtems_scheduler_get_processor()` instead.

* The obsoleted `rtems_get_processor_count()` directive was removed.  Use
  `rtems_scheduler_get_processor_maximum()` instead.

* The obsoleted `boolean` type was removed.  Use `bool` instead.

* The obsoleted `single_precision` type was removed.  Use `float` instead.

* The obsoleted `double_precision` type was removed.  Use `double` instead.

* The obsoleted `proc_ptr` type was removed.  Use a proper function pointer
  type.

* The obsoleted `rtems_context` type was removed.

* The obsoleted `rtems_context_fp` type was removed.

* The obsoleted `rtems_extension` type was removed.  Use `void` instead.

* The obsoleted `rtems_io_lookup_name()` type was removed. Use `stat()`
  instead.

* The obsoleted `region_information_block` was removed.  Use
  `Heap_Information_block` instead.

* The obsoleted `rtems_thread_cpu_usage_t` type was removed. Use
  `struct timespec` instead.

* The obsoleted `rtems_rate_monotonic_period_time_t` type was removed. Use
  `struct timespec` instead.

* The obsoleted `RTEMS_MAXIMUM_NAME_LENGTH` define was removed. Use
  `sizeof(rtems_name)` instead.

### SMP Support Improvements

* The SMP EDF scheduler affinity handling was improved to ensure FIFO fairness.

* The SMP scheduler framework was reworked to fix potential data corruption
  issues and priority group ordering violations.

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

* The obsolete libmisc/serdbg was removed. Use libdebugger instead. This functionality
  was not built as part of the 5 release series in anticipation of its removal.

## Architectures

Removed obsoleted architectures:

* Epiphany

* PowerPC SPE

Obsoleted architectures:

* V850
* SPARC64
* SuperH (sh)

## BSPs and Device Drivers

* General

    * TBD

* New BSPs

    * `arm/fvp`

    * `arm/imxrt`

    * `arm/stm32h7`

    * `arm/xilinx-zynqmp-rpu`

* Significant updates to existing BSPs

    * `ARCH/BSP`: TBD

* Removal of obsoleted BSPs

    * `powerpc/brs5l`

    * `powerpc/brs6l`

    * `powerpc/dp2`

    * `powerpc/haleakala`

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

* Add `futimens()` and `utimensat()`

## Ecosystem

* Improved GCOV support for RTEMS and embedded systems in general.  See GCC
  options `-fprofile-info-section` and `-fprofile-update=atomic`.  The
  `libgcov` provides now the `__gcov_info_to_gcda()` function to dump the GCOV
  information.
