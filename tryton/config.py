# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
import configparser
import gettext
import locale
import logging
import optparse
import os
import sys

from gi.repository import GdkPixbuf

from tryton import __version__

_ = gettext.gettext


def get_config_dir():
    if os.name == 'nt':
        appdata = os.environ['APPDATA']
        if not isinstance(appdata, str):
            appdata = str(appdata, sys.getfilesystemencoding())
        return os.path.join(appdata, '.config', 'tryton',
                __version__.rsplit('.', 1)[0])
    config_path = os.getenv('XDG_CONFIG_HOME', os.path.join('~', '.config'))
    return os.path.expanduser(
        os.path.join(config_path, 'tryton', __version__.rsplit('.', 1)[0]))


if not os.path.isdir(get_config_dir()):
    os.makedirs(get_config_dir(), 0o700)


class ConfigManager(object):
    "Config manager"

    def __init__(self):
        demo_server = 'coog'
        demo_database = 'demo'
        self.defaults = {
            'login.profile': demo_server,
            'login.login': 'demo',
            'login.service': '',
            'login.service.port': 8001,
            'login.host': demo_server,
            'login.db': demo_database,
            'login.expanded': False,
            'login.date': False,
            'tip.autostart': False,
            'tip.position': 0,
            'form.toolbar': True,
            'client.title': 'Coog',
            'client.default_width': 900,
            'client.default_height': 750,
            'client.modepda': False,
            'client.toolbar': 'default',
            'client.save_tree_width': True,
            'client.save_tree_state': False,
            'client.spellcheck': False,
            'client.lang': locale.getdefaultlocale()[0],
            'client.language_direction': 'ltr',
            'client.email': '',
            # JCA: Set default limit to 100 for performances
            'client.limit': 100,
            'client.check_version': False,
            'client.bus_timeout': 10 * 60,
            'icon.colors': '#0094d2,#57a639,#cc0000',
            'tree.colors': '#777,#dff0d8,#fcf8e3,#f2dede',
            'calendar.colors': '#fff,#3465a4',
            'graph.color': '#3465a4',
            'image.max_size': 10 ** 6,
            'image.cache_size': 1024,
            'bug.url': 'https://support.coopengo.com/',
            'download.url': 'https://downloads-cdn.tryton.org/',
            'download.frequency': 60 * 60 * 8,
            'menu.pane': 200,
        }
        self.config = {}
        self.options = {}
        self.arguments = []

    def parse(self):
        parser = optparse.OptionParser(version=("Coog %s" % __version__),
                usage="Usage: %prog [options] [url]")
        parser.add_option("-c", "--config", dest="config",
                help=_("specify alternate config file"))
        parser.add_option("-d", "--dev", action="store_true",
                default=False, dest="dev",
                help=_("development mode"))
        parser.add_option("-v", "--verbose", action="store_true",
                default=False, dest="verbose",
                help=_("logging everything at INFO level"))
        parser.add_option("-l", "--log-level", dest="log_level",
                help=_("specify the log level: "
                "DEBUG, INFO, WARNING, ERROR, CRITICAL"))
        parser.add_option("-o", "--log-ouput", dest="log_output", default=None,
            help=_("specify the file used to output logging information"))
        parser.add_option("-u", "--user", dest="login",
                help=_("specify the login user"))
        parser.add_option("-s", "--server", dest="host",
                help=_("specify the server hostname:port"))
        opt, self.arguments = parser.parse_args()
        self.rcfile = opt.config or os.path.join(
            get_config_dir(), 'tryton.conf')
        self.load()

        logging_config = {
            'format': '%(asctime)s.%(msecs)03d:%(levelname)s:%(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
            }
        if opt.log_output:
            logging_config['filename'] = opt.log_output

        loglevels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL,
            }
        if not opt.log_level:
            if opt.verbose:
                opt.log_level = 'INFO'
            else:
                opt.log_level = 'ERROR'
        logging_config['level'] = loglevels[opt.log_level.upper()]
        logging.basicConfig(**logging_config)

        self.options['dev'] = opt.dev
        for arg in ['login', 'host']:
            if getattr(opt, arg):
                self.options['login.' + arg] = getattr(opt, arg)

    def save(self):
        try:
            parser = configparser.ConfigParser()
            for entry in list(self.config.keys()):
                if not len(entry.split('.')) == 2:
                    continue
                section, name = entry.split('.')
                if not parser.has_section(section):
                    parser.add_section(section)
                parser.set(section, name, str(self.config[entry]))
            with open(self.rcfile, 'w') as fp:
                parser.write(fp)
        except IOError:
            logging.getLogger(__name__).warn(
                _('Unable to write config file %s.')
                % (self.rcfile,))
            return False
        return True

    def load(self):
        parser = configparser.ConfigParser()
        parser.read([self.rcfile])
        for section in parser.sections():
            for (name, value) in parser.items(section):
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                if section == 'client' and name == 'limit':
                    # First convert to float to be backward compatible with old
                    # configuration
                    value = int(float(value))
                self.config[section + '.' + name] = value
        return True

    def __setitem__(self, key, value, config=True):
        self.options[key] = value
        if config:
            self.config[key] = value

    def __getitem__(self, key):
        return self.options.get(key, self.config.get(key,
            self.defaults.get(key)))


CONFIG = ConfigManager()
CURRENT_DIR = os.path.dirname(__file__)
if hasattr(sys, 'frozen'):
    CURRENT_DIR = os.path.dirname(sys.executable)
if not isinstance(CURRENT_DIR, str):
    CURRENT_DIR = str(CURRENT_DIR, sys.getfilesystemencoding())

PIXMAPS_DIR = os.path.join(CURRENT_DIR, 'data', 'pixmaps', 'tryton')
if not os.path.isdir(PIXMAPS_DIR):
    # do not import when frozen
    import pkg_resources
    PIXMAPS_DIR = pkg_resources.resource_filename(
        'tryton', 'data/pixmaps/tryton')

TRYTON_ICON = GdkPixbuf.Pixbuf.new_from_file(
    os.path.join(PIXMAPS_DIR, 'coog_no_text.svg'))
