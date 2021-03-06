from ConfigParser import RawConfigParser
import logging
import os
import sys

NAMED_REPOS = dict(
    collective = ('collective:', 'https://svn.plone.org/svn/collective/', 'svn'),
    github = ('github:', 'git://github.com/', 'git'),
    )

logger = logging.getLogger("mr.developer")


class WCError(Exception):
    """ A working copy error. """


workingcopytypes = {}

class BaseWorkingCopy(object):
    def __new__(cls, kind):
        wc = object.__new__(cls)
        workingcopytypes[kind] = wc
        return wc


class WorkingCopies(object):
    def __init__(self, sources):
        self.sources = sources

    def checkout(self, packages, **kwargs):
        errors = False
        for name in packages:
            if name not in self.sources:
                logger.error("Checkout failed. No source defined for '%s'." % name)
                sys.exit(1)
            source = self.sources[name]
            try:
                kind = source['kind']
                wc = workingcopytypes.get(kind)
                if wc is None:
                    logger.error("Unknown repository type '%s'." % kind)
                    sys.exit(1)
                output = wc.checkout(source, **kwargs)
                if kwargs.get('verbose', False) and output is not None and output.strip():
                    print output
            except WCError, e:
                for l in e.args[0].split('\n'):
                    logger.error(l)
                sys.exit(1)
        return errors

    def matches(self, source):
        name = source['name']
        if name not in self.sources:
            logger.error("Checkout failed. No source defined for '%s'." % name)
            sys.exit(1)
        source = self.sources[name]
        try:
            kind = source['kind']
            wc = workingcopytypes.get(kind)
            if wc is None:
                logger.error("Unknown repository type '%s'." % kind)
                sys.exit(1)
            return wc.matches(source)
        except WCError, e:
            for l in e.args[0].split('\n'):
                logger.error(l)
            sys.exit(1)

    def status(self, source, **kwargs):
        name = source['name']
        if name not in self.sources:
            logger.error("Status failed. No source defined for '%s'." % name)
            sys.exit(1)
        source = self.sources[name]
        try:
            kind = source['kind']
            wc = workingcopytypes.get(kind)
            if wc is None:
                logger.error("Unknown repository type '%s'." % kind)
                sys.exit(1)
            return wc.status(source, **kwargs)
        except WCError, e:
            for l in e.args[0].split('\n'):
                logger.error(l)
            sys.exit(1)

    def update(self, packages, **kwargs):
        for name in packages:
            if name not in self.sources:
                continue
            source = self.sources[name]
            try:
                kind = source['kind']
                wc = workingcopytypes.get(kind)
                if wc is None:
                    logger.error("Unknown repository type '%s'." % kind)
                    sys.exit(1)
                output = wc.update(source, **kwargs)
                if kwargs.get('verbose', False) and output is not None and output.strip():
                    print output
            except WCError, e:
                for l in e.args[0].split('\n'):
                    logger.error(l)
                sys.exit(1)


class Config(object):
    def __init__(self, buildout_dir, sources_dir=None):
        self.cfg_path = os.path.join(buildout_dir, '.mr.developer.cfg')
        self._config = RawConfigParser()
        self._config.optionxform = lambda s: s
        self._config.read(self.cfg_path)
        if sources_dir is not None:
            self.sources_dir = sources_dir
        self.develop = {}
        self.buildout_args = []
        self.rewrites = {
                'defaultcfg': [],
                'local': []
                }
        self.namedrepos = NAMED_REPOS
        if self._config.has_section('develop'):
            for package, value in self._config.items('develop'):
                value = value.lower()
                if value == 'true':
                    self.develop[package] = True
                elif value == 'false':
                    self.develop[package] = False
                elif value == 'auto':
                    self.develop[package] = 'auto'
                else:
                    raise ValueError("Invalid value in 'develop' section of '%s'" % self.cfg_path)
        if self._config.has_option('buildout', 'args'):
            args = self._config.get('buildout', 'args').split("\n")
            for arg in args:
                arg = arg.strip()
                if arg.startswith("'") and arg.endswith("'"):
                    arg = arg[1:-1].replace("\\'", "'")
                elif arg.startswith('"') and arg.endswith('"'):
                    arg = arg[1:-1].replace('\\"', '"')
                self.buildout_args.append(arg)
        if self._config.has_option('mr.developer', 'rewrites'):
            for rewrite in self._config.get('mr.developer', 'rewrites').split('\n'):
                self.rewrites['local'].append(rewrite.split())

        # rewrites from default.cfg
        defaultcfg_path = os.path.join(os.path.expanduser('~'),
                '.buildout', 'default.cfg')
        if os.path.exists(defaultcfg_path):
            defaultcfg = RawConfigParser()
            # no idea what this does - copy pasted from above
            defaultcfg.optionxform = lambda s: s
            defaultcfg.read(defaultcfg_path)
            if defaultcfg.has_option('mr.developer', 'rewrites'):
                for rewrite in defaultcfg.get('mr.developer', 'rewrites').split('\n'):
                    self.rewrites['defaultcfg'].append(rewrite.split())

    def save(self):
        self._config.remove_section('develop')
        self._config.add_section('develop')
        for package in sorted(self.develop):
            state = self.develop[package]
            if state is 'auto':
                self._config.set('develop', package, 'auto')
            elif state is True:
                self._config.set('develop', package, 'true')
            elif state is False:
                self._config.set('develop', package, 'false')

        if not self._config.has_section('buildout'):
            self._config.add_section('buildout')
        self._config.set('buildout', 'args', "\n".join(repr(x) for x in self.buildout_args))

        if not self._config.has_section('mr.developer'):
            self._config.add_section('mr.developer')
        self._config.set('mr.developer', 'rewrites',
                "\n".join(" ".join(x) for x in self.rewrites['local']))

        self._config.write(open(self.cfg_path, "w"))
