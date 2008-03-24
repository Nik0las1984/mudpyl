==============================
Logging to HTML files
==============================

Logging your MUDding sessions is really easy in mudpyl. A module has already
been written that does the hard work of generating HTML: ``library/html.py``
is its name.

To use it, first import the mudpyl module that handles all the messy stuff::

    from mudpyl.library.html import HTMLLoggingModule

Now, to use this, inherit your ``MainModule`` from ``HTMLLoggingModule``,
instead of from ``BaseModule``. By default, this dumps logs into 
~/logs/*character name*/, using a time-based filename. However, this is 
overrideable: first, the ``logplace`` attribute is passed into time.strftime,
then it is %-formatted using a dictionary. Currently, the only entry in the
dict is ``'name'``, which is the ``name`` attribute of the module.

An example, using all the defaults::

    class MainModule(HTMLLoggingModule):
        #etc

Logging to /var/mudlogs/*name*/*date and time of connection*.html::

    class MainModule(HTMLLoggingModule):
        logplace = '/var/logs/%%(name)s/%Y-%m-%dT%H:%M:%S.html

Because the string will be put through strftime and then %-formatted, the
``name`` placeholder has to be escaped.