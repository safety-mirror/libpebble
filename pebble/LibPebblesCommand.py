import fnmatch
import logging
import os
import sh
import time

import pebble as libpebble

from PblCommand import PblCommand

PEBBLE_PHONE_ENVVAR='PEBBLE_PHONE'

class LibPebbleCommand(PblCommand):

    def configure_subparser(self, parser):
        PblCommand.configure_subparser(self, parser)
        phone_default = os.getenv(PEBBLE_PHONE_ENVVAR)
        phone_required = False if phone_default else True
        parser.add_argument('--phone', type=str, default=phone_default, required=phone_required, help='The host of the WebSocket server to connect')

    def run(self, args):
        self.pebble = libpebble.Pebble()
        self.pebble.connect_via_websocket(args.phone)

class PblPingCommand(LibPebbleCommand):
    name = 'ping'
    help = 'Ping your Pebble project to your watch'

    def configure_subparser(self, parser):
        LibPebbleCommand.configure_subparser(self, parser)

    def run(self, args):
        LibPebbleCommand.run(self, args)
        self.pebble.ping(cookie=0xDEADBEEF)

class PblInstallCommand(LibPebbleCommand):
    name = 'install'
    help = 'Install your Pebble project to your watch'

    def get_pbw_path(self):
        return 'build/{}.pbw'.format(os.path.basename(os.getcwd()))

    def configure_subparser(self, parser):
        LibPebbleCommand.configure_subparser(self, parser)
        parser.add_argument('pbw_path', type=str, nargs='?', default=self.get_pbw_path(), help='Path to the pbw to install (ie: build/*.pbw)')
        parser.add_argument('--logs', action='store_true', help='Display logs after installing the app')

    def run(self, args):

        if not os.path.exists(args.pbw_path):
            logging.error("Could not find pbw <{}> for install.".format(args.pbw_path))
            return 1

        LibPebbleCommand.run(self, args)
        self.pebble.install_app_ws(args.pbw_path)

        if args.logs:
            logging.info('Displaying logs ... Ctrl-C to interrupt.')
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                return


class PblListCommand(LibPebbleCommand):
    name = 'list'
    help = 'List the apps installed on your watch'

    def configure_subparser(self, parser):
        LibPebbleCommand.configure_subparser(self, parser)

    def run(self, args):
        LibPebbleCommand.run(self, args)

        try:
            response = self.pebble.get_appbank_status()
            apps = response['apps']
            if len(apps) == 0:
                logging.info("No apps installed.")
            for app in apps:
                logging.info('[{}] {}'.format(app['index'], app['name']))
        except:
            logging.error("Error getting apps list.")
            return 1

class PblRemoveCommand(LibPebbleCommand):
    name = 'rm'
    help = 'Remove an app from your watch'

    def configure_subparser(self, parser):
        LibPebbleCommand.configure_subparser(self, parser)
        parser.add_argument('bank_id', type=int, help="The bank id of the app to remove (between 1 and 8)")

    def run(self, args):
        LibPebbleCommand.run(self, args)

        for app in self.pebble.get_appbank_status()['apps']:
            if app['index'] == args.bank_id:
                self.pebble.remove_app(app["id"], app["index"])
                logging.info("App removed")
                return 0

        logging.info("No app found in bank %u" % args.bank_id)
        return 1


class PblLogsCommand(LibPebbleCommand):
    name = 'logs'
    help = 'Continuously displays logs from the watch'

    def configure_subparser(self, parser):
        LibPebbleCommand.configure_subparser(self, parser)

    def run(self, args):
        LibPebbleCommand.run(self, args)
        self.pebble.app_log_enable()

        logging.info('Displaying logs ... Ctrl-C to interrupt.')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print "\n"
            self.pebble.app_log_disable()
            return
