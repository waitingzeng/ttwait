
import sys
import os
from pyphantomjs import pyphantomjs
from pyphantomjs import __version__
from pyphantomjs.arguments import parseArgs
from phantom import Phantom

# make keyboard interrupt quit program
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

def main(arguments):
    app = pyphantomjs.QApplication([sys.argv[0]] + arguments)

    app.setApplicationName('PyCommPhantomJS')
    app.setOrganizationName('TTwait')
    app.setApplicationVersion(__version__)

    args = parseArgs(app, arguments)

    phantom = Phantom(app, args)

    pyphantomjs.do_action('Main')

    if phantom.execute():
        app.exec_()
    return phantom.returnValue()



if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

