# RTEMS Project Release Scripts.

These scripts release RTEMS. They are tested and run on FreeBSD.

To run:
```shell
$ ./rtems-release 6 1-rc1
```

## Gitlab API Access

A release builds the release notes from Gitlab. The data is fetched
from the Gitlab API using an API key. Please refer to the Gitlab
documentation to add an API key your account. You only need read
access.

Create a `config.ini` file with your key. The format is:

```
[global]
default = rtems
ssl_verify = true
timeout = 10

[rtems]
url = https://gitlab.rtems.org
oauth_token = rtemsgl-AKEYOFCHARACTERS
```

Do not place this file in this releases directory and do not added it
to git.

## Set Up

Releases are made and tested on a FreeBSD machine. These scripts
should work on any hosts however no testing has been done on other
systems.

1. Install `git`.

2. Create a `python3` vritual envronment:

   ```shell
   $ python3 -m venv release-py
   ```

3. Install the python modules using `pip` in the virtualenv:

   ```shell
   . ./release-py/bin/activate
   ```

   ```shell
   pip install sphinx sphinxcontrib-bibtex sphinx_inline_tabs \
               myst_parser \
               furo \
               python-gitlab
   ```

4. Install `npm` and the install the HTML inliner:

   ```
   # npm install inliner
   ```

5. Install `pandoc` for Markdown

6. PDF Release notes require the same set up as RTEMS
   Documentation. Please refer to the documentation in the
   `rtems-docs` repository and follow the set up procedure for PDF it
   has.
