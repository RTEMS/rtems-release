## RTEMS 5.2 Release Notes

### API Changes

* Termios
  * `txTaskCharsDequeued` has been added to `struct rtems_termios_tty`. With
    that the size of the structure changed. Libraries and applications that use
    the structure should be recompiled.
  * The `l_start` line discipline function now receives the number of characters
    that have been sent. It is save to ignore the extra parameter for
    applications that don't need it.

#### API Additions

* NTP support
  * Addition of NTP update second handler via _Timecounter_Set_NTP_update_second() from <rtems/score/timecounter.h>
