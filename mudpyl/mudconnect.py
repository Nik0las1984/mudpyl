#!/usr/bin/python
"""Connand-line script to hook you up to the MUD of your choice."""
from mudpyl.net.telnet import TelnetClientFactory
from mudpyl.modules import load_file
from mudpyl import __version__
import argparse

parser = argparse.ArgumentParser(version = "%(prog)s " + __version__, 
                                 prog = 'mudpyl')

known_guis = ['gtk']
gui_help = ("The GUI to use. Available options: %s. Default: %%(default)s" %
                     ', '.join(known_guis))

parser.add_argument('-g', '--gui', default = 'gtk', help = gui_help,
                    choices = known_guis)
parser.add_argument("modulename", help = "The module to import")
parser.add_argument("--profile", action = "store_true",  default = False,
                    help = "Whether to profile exection. Default: False")

def main():   
    """Launch the client.

    This is the main entry point. This will first initialise the GUI, then
    load the main module specified on the command line.
    """
    options = parser.parse_args()

    modclass = load_file(options.modulename)
    factory = TelnetClientFactory(modclass.name, modclass.encoding, 
                                  options.modulename)

    if options.gui == 'gtk':
        from mudpyl.gui.gtkgui import configure

    configure(factory)

    modinstance = factory.realm.load_module(modclass)
    modinstance.is_main()

    from twisted.internet import reactor

    #pylint kicks up a major fuss about these lines, but that's because 
    #Twisted does some hackery with the reactor namespace.
    #pylint: disable-msg=E1101

    reactor.connectTCP(modclass.host, modclass.port, factory)
    if not options.profile:
        reactor.run()
    else:
        import cProfile
        cProfile.runctx("reactor.run()", globals(), locals(),
                        filename = "mudpyl.prof")

if __name__ == '__main__':
    main()
