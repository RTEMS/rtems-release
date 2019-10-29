RTEMS Project Release Scripts.

Chris Johns <chrisj@rtems.org>
Date: November 2019

These scripts release the RTEMS kernel. They are tested and run on the
RTEMS Project FreeBSD server.

To run:

  $ ./rtems-release 5 0.0-m1911

Set Up
------

Releases are made on a FreeBSD machine. These scripts should work on
any hosts however no testing has been done on other systems.

1. Install git.

2. Crate a python3 vritualenv set up. If python3 is the system default
   the --python option is not needed:

    $ virtualenv --python=python3 release

3. Install sphinx using pip in the virtualenv:

   $ . ./release/bin/activate
   (release) $ pip install sphinx
   (release) $ pip install sphinxcontrib-bibtex

4. Install npm and the install the HTML inliner:

   # npm install inliner
