.. contents:: :depth: 1

Introduction
============

.. figure:: http://www.netsight.co.uk/junk/xkcd-buildout.png
    :figwidth: image

    Let Mr. Developer help you win the everlasting buildout battle!

    (Remixed by Matt Hamilton, original from http://xkcd.com/303)

``mr.developer`` is a ``zc.buildout`` extension which makes it easier to work with
buildouts containing lots of packages of which you only want to develop some.
The basic idea for this comes from Wichert Akkerman's ``plonenext`` effort.


Usage
=====

You add ``mr.developer`` to the ``extensions`` option of your ``[buildout]``
section. Then you can add the following options to your ``[buildout]``
section:

  ``sources-dir``
    This specifies the default directory where your development packages will
    be placed. Defaults to ``src``.

  ``sources``
    This specifies the name of a section which lists the repository
    information of your packages. Defaults to ``sources``.

  ``auto-checkout``
    This specifies the names of packages which should be checked out during
    buildout, packages already checked out are skipped. You can use ``*`` as
    a wild card for all packages in ``sources``.

The format of the section with the repository information is::

  <name> = <kind> <url> [path] [revision=<revspec>] [pkgbasedir=[<pkgbasedir>]]

Where <name> is the package name and <kind> is either ``svn``, ``hg`` or
``git``, <url> is the location of the repository and the optional [path]
is the base directory where the repository will be checked out (the name of
the package will be appended), if it's missing, then ``sources-dir`` will
be used. It's also possible to use ``fs`` as <kind>, then the format is
"<name> = <kind> <name> [path]", where <name> is the package name and
it's duplicated as an internal sanity check (it was also easier to keep
the format the same :) ). This allows you for example to start a new
package which isn't in version control yet.

For an explanation of revision and basedir parameters see below.


The following is an example of how your ``buildout.cfg`` may look like::

  [buildout]
  ...
  extensions = mr.developer
  sources = sources
  auto-checkout = my.package

  [sources]
  my.package = svn http://example.com/svn/my.package/trunk
  some.other.package = git git://example.com/git/some.other.package.git

When you run buildout, you will get a script at ``bin/develop`` in your
buildout directory. With that script you can perform various actions on the
packages, like checking out the source code, without the need to know where
the repository is located.

For help on what the script can do, run ``bin/develop help``.

If you checked out the source code of a package, you need run buildout again.
The package will automatically be marked as an develop egg and, if it's listed
in the section specified by the ``versions`` option in the ``[buildout]``
section, the version will be cleared, so the develop egg will actually be
used. You can control the list of develop eggs explicitely with the
``activate`` and ``deactivate`` commands of ``bin/develop``.


Project repositories
--------------------

``pkgbasedir`` exists to support *project repositories*, i.e. repositories that do
not directly contain the egg, but hold multiple eggs in seperate directories
optionally further grouped into subdirectories.


Given a project repository with the following structure::

  example.projectrepo.git/
    example.projectrepo.pkg1/
      setup.py
      src/
        example/
          projectrepo/
            pkg1/
    subdir/
      example.projectrepo.pkg2/
        setup.py
        src/
          example/
            projectrepo/
              pkg2/

You would access the packages::

  [sources]
  example.projectrepo.pkg1 =
    git git://github.com/chaoflow/example.projectrepo.git pkgbasedir=
  example.projectrepo.pkg2 =
    git git://github.com/chaoflow/example.projectrepo.git pkgbasedir=subdir

Project repo support so far has been tested with git and svn, but should work
with mercurial - FEEDBACK please.


Revision support
----------------

Subversion supports checkout of specific revisions/tags and following branches
via repository url. Some examples::

  example.svnpackagerepo = svn collective:example.svnpackagerepo/trunk@100499

  example.svnpackagerepo = svn collective:example.svnpackagerepo/branches/stable

  example.svnpackagerepo = svn collective:example.svnpackagerepo/tags/1.1


Preliminary support to check out specific revisions exists for git.

Valid ``revspec``s are:

- SHA1 of a revision
- name of a local tag/branch
- name of a remote branch which will automatically be set up as a local
  tracking branch with the same name

Some examples::

  example.packagerepo =
    git git://github.com/chaoflow/example.packagerepo.git rev=master
  example.packagerepo =
    git git://github.com/chaoflow/example.packagerepo.git revision=stable
  example.packagerepo =
    git git://github.com/chaoflow/example.packagerepo.git revision=50e34


Named repositories
------------------

Named repositories save typing, e.g.::

  example.svnpackagerepo = svn collective:example.svnpackagerepo/trunk

Via rewrite (see below) this is translated to::

  example.svnpackagerepo = svn https://svn.plone.org/svn/collective/example.svnpackagerepo/trunk

The structure of a url using a named repository is::

  <reponame>:<relative_path>

Mr. Developer knows the following named repositories::

  collective https://svn.plone.org/svn/collective/


Rewrites
--------

Rewrites are peformed on the url before fetching the repository and are read
from ~/.buildout/default.cfg and <buildoutdir>/.mr.developer.cfg.

In contrast to buildout.cfg syntax, rewrite definitions are additive.

A typical use case for rewrites is to change public fetch urls to your
personal pull/push url.::

  [mr.developer]
  rewrites =
      git://github.com/ git@github.com:

Rewrites are performed in the order defined, local rewrites preceeding
default.cfg rewrites.

Normally a rewrite is matched to and performed on the beginning of a url.

It is also possible to rewrite using regular expressions::

  [mr.developer]
  rewrites =
      re.sub  ^(.*)somepath/(.*)$  \1\2
      re.sub  .git$

The arguments are directly passed to python's re.sub function. If the last
argument (the replacement string) is missing, an empty string is assumed - the
second example would remove a .git at the end of urls.

The named repositories are implemented by using rewrites. These are performed
before your rewrites, i.e. you can perform rewrites on the actual
urls.::

- named repository rewrites
- your local rewrites (.mr.developer.cfg)
- default.cfg rewrites


Troubleshooting
===============

Dirty SVN
---------

You get an error like::

  ERROR: Can't switch package 'foo' from 'https://example.com/svn/foo/trunk/', because it's dirty.

If you have not modified the package files under src/foo, then you can check
what's going on with `status -v`. One common cause is a `*.egg-info` folder
which gets generated every time you run buildout and this shows up as an
untracked item in svn status.

You should add .egg-info to your global Subversion ignores in
`~/.subversion/config`, like this::
  
  global-ignores = *.o *.lo *.la *.al .libs *.so *.so.[0-9]* *.a *.pyc *.pyo *.rej *~ #*# .#* .*.swp .DS_Store *.egg-info

HTTPS certificates
------------------

The best way to handle https certificates at the moment, is to accept them
permanently when checking out the source manually.
