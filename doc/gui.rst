=====================================
Using mudpyl's GUI
=====================================

mudpyl has two GUIs written for it: one using the wxPython toolset, and the
other using the PyGTK toolset. Both intend to support the same functionality,
but the wxgui in particular has infelicities. Therefore, the gtkgui is
recommended and is the default.

Picking which GUI to use
========================

When the client is started from the command line, the command looks something
like this::

    mudconnect.py fred

This will launch the default GUI, which is the gtkgui. To use a different GUI,
the ``--gui`` switch must be specified. This command will use the wxgui::

    mudconnect.py --gui wx fred

``--gui`` may be shortened to just ``-g``. Also, the default GUI may be 
explicitly specified, like so::

    mudconnect.py -g gtk fred

The keybindings
===============

mudpyl has a number of default keybindings, in addition to those the toolkit
provides by default. These are found in ``gui/bindings.py``. They are not
actually loaded by default, but should probably be done anyway. They are:

Page Up and Page Down:
    Because the command line is only one line, these would be no-ops. However,
    they are forwarded to the output window.
Return:
    This sends the current text of the command line to the MUD, adds this text
    to the command history, then clears the command line.
Escape:
    This adds the current text of the command line to the history and clears 
    it, but does not send anything to the MUD.
Up and Down:
    These keys move backwards and forwards, respectively, in the command 
    history, replacing the current value of the command line with previous
    commands.
Tab:
    The GUI stores a listing of words that have been displayed on screen,
    ordered by how recently they've been seen. When tab is pressed, the word
    currently under the cursor is read. The first word in the list that this
    word is a prefix of will be put into the command line instead of the 
    current word. Example:

    The value of the command line is ``foo``; ``foobar`` has been sent by the
    MUD previously. The user presses tab, and the word ``foo`` is changed to
    ``foobar``. Try it and see how it works for yourself!
Pause/Break:
    This key toggles the automatic scrolling of the output window to new text.
    Useful for trying to read something when it's a bit busy.

The display
===========

The GUI has three main parts: the output window (the largest part, where all
the MUD's text goes), the command line (where you type in your commands), and
the status bar (which displays a few pieces of useful information). On the
status bar, there is a count of how long the connection has lasted, and a
reminder about the screen being paused, if it is.
