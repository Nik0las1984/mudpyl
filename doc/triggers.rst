======================
Understanding Triggers
======================

Triggers are the primary way that your program will receive information from
the MUD. Fundamentally, they are very simple: a trigger has two methods:
``match`` and ``__call__``, and one attribute, ``sequence``.

mudpyl provides a class, ``RegexTrigger``, that provides most of the plumbing 
that's needed, as well as a few other classes and functions to make life 
simpler.

Generic API
===========

``match``
---------

``match`` is the method that defines when the callback will be run. It takes
one parameter, a Metaline, which is the line from the MUD that is being 
matched against. Its return value is a sequence, with each element standing
for a single match. These elements will be passed individually as parameters
to the callback.

This may be overridden to, for example, only fire the trigger if the MUD's
line is a certain colour, or a certain minimum length.

``__call__``
------------

Triggers must be callable, and take two parameters: an element of the sequence
returned by ``match``, and the ``TriggerMatchingRealm`` that is doing the
matching. The return value of this function is not defined.

``sequence``
------------

This is a number representing the trigger's absolute position in the execution
order. Lower numbers will be run first, and the order is not defined if two
triggers have the same sequence.

RegexTrigger
============

``RegexTrigger`` is a regular Python class. Its regular expression is stored
in a variable named ``regex`` and its callback in an attribute named ``func``.
If ``regex`` is None, the empty list is returned, effectively disabling it.
The callback is actually wrapped for some error handling and minor nicities,
but this is a very thin layer. These variables may be overridden by 
inheritance::

    class FooTrigger(RegexTrigger):
        regex = re.compile("[fF]oo!")
        sequence = -20
        def func(self, match, realm):
            realm.write("FOO WAS SEEN!")

    trigger = FooTrigger()

This is similar to the below code, but with more error checking provided by 
the wrapper around ``func``::

    class FooTrigger(object):
        def match(self, line):
            return re.finditer('[fF]oo', line)
        sequence = -20
        def __call__(self, match, realm):
            realm.write("FOO WAS SEEN")

They may also be defined when creating an instance::

    def func(match, realm):
        realm.write("BAR WAS SEEN!")

    trigger = RegexTrigger(func = func, regex = "bar", sequence = -15)

These argunemts will be bound as attributes of the instance, and will behave
normally.

In all the above examples, ``sequence`` is optional, and defaults to 0.

Useful decorators
=================

Two decorators are provided for turning ordinary functions and methods into
triggers: ``binding_trigger`` and ``non_binding_trigger``. They are roughly
analogous to the difference between bound methods and unbound functions.

``non_binding_trigger``
-----------------------

This is fairly simple: it takes two arguments, ``regex`` and ``sequence``
(in that order, and ``sequence`` is optional). After decorating the function,
a factory function producing ``RegexTrigger`` instances with the given values.

Example::

    @non_binding_trigger("spam")
    def viking_chorus(match, realm):
        realm.write("SPAM SPAM SPAM SPAM")

    trigger = viking_chorus()

``binding_trigger``
-------------------

This decorator is more complicated. The arguments taken are the same as above.
However, this does not directly create triggers by calling. The final return
value should always be attached to a class: when the return value is accessed
as an attribute, the wrapped function is 'bound' like a method, and then
a ``RegexTrigger`` is created. These are cached on a per-object basis.

These use the descriptor protocol, so can only be used with new-style classes.

Example::

    class Viking(object):
        @binding_trigger("spam")
        def spam_sighted(self, match, realm):
            realm.send("adjust helmet")
            realm.send("quaff mead")
            realm.send("sing about spam")

    viking = Viking()
    trigger = viking.spam_sighted

As these are cached, every time ``viking.spam_sighted`` is accessed, the same
trigger will be returned. However, ``another_viking.spam_sighted`` returns a
different trigger.

Altering the client's behaviour
===============================

Running code when we see certain things from the MUD is all well and good, and
in most cases does everything that we'll need it to. But, sometimes, some part
of the client's behaviour needs to be changed. This is done by setting certain
flags or calling certain methods on the ``realm`` argument to the callback.

Stopping the line from being displayed
--------------------------------------

This is controlled by an attribute of the ``realm``, ``display_line``, which
is by default ``True``.

Altering the line
-----------------

While the ``realm`` has an attribute, ``metaline``, which can be directly
altered by triggers, this is a very Bad Idea, as other triggers may also want
to change the line. This attribute should be accessed **read only**.

To actually change a line, use the ``alterer`` attribute of the ``realm``. It
shares the destructive API (e.g., methods like ``change_fore`` and ``insert``)
with ``Metaline``, but buffers each alteration until after all triggers have
been run. It accounts for deletions and insertions, making sure that triggers
do not inadvertently change the wrong piece of text.
