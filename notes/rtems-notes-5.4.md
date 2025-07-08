## RTEMS 5.4 Release Notes

### Source Builder

All build sets depending on github.com, git.rtems.org, and devel.rtems.org have
been migrated to use the appropriate resources on gitlab.rtems.org. As part of
this process, the SIS build set has been modified to use a rtems-sis-2.21
tarball instead of a sis-2.21 tarball as that is the new name for the project in
the RTEMS GitLab infrastructure. The contents of the tarball are identical to
the previously generated tarballs except for the root path.
