============================================
Churro: Simple Filesystem Object Persistence
============================================

`Churro` is a simplistic persistent storage for Python objects which stores a 
tree of hierchically nested objects as folders and flat files in a filesystem.
Churro uses `AcidFS <http://pypi.python.org/pypi/acidfs/1.0b2>`_ to provide 
ACID transaction semantics.  Changes to any `Churro` object tree are only 
persisted when a transaction successfully commits.  `Churro` uses JSON to 
serialize objects.  `Churro` is meant to be lightweight and durable.  Use of 
JSON, a universally understood and human readable text file format, insures that
data stored by `Churro` is portable to other applications and platforms across
space and time.

In addition to these docs, it couldn't hurt to look over the `AcidFS 
documentation <http://acidfs.readthedocs.org/>`_.

Defining Persistent Types
=========================

In order for an object to be saved in a `Churro` repository, it must inherit 
from :class:`~churro.Persistent` or 
:class:`~churro.PersistentFolder`.  Attributes of your 
persistent objects that you want to be persisted must be derived from 
:class:`~churro.PersistentProperty`.  Probably the best way to illustrate is by 
example, so let's say you're writing an application that saves contacts in an 
address book.  We might write some code that looks like this::

    from churro import Persistent
    from churro import PersistentProperty
    from churro import PersistentFolder

    class AddressBook(PersistentFolder):
        title = PersistentProperty()

        def __init__(self, title):
            self.title = title

    class Contact(Persistent):
        name = PersistentProperty()
        address = PersistentProperty()

        def __init__(self, name, address):
            self.name = name
            self.address = address

You can see that defining your persistent types is pretty straightforward.  Next
you'll want to open a repository and start storing some data.

Adding Objects to the Repository
================================

::

    from churro import Churro

    repo = Churro('/path/to/folder')
    root = repo.root()
    contacts = AddressBook('My Contacts')
    root['contacts'] = contacts

    contacts['fred'] = Contact('Fred Flintstone', '1 Rocky Road')
    contacts['barney'] = Contact('Barney Rubble', '6 Bronto Lane')

Above, we create an instance of :class:`Churro <churro.Churro>` where the 
argument is the folder in the filesystem where the repository will live.  If the
folder does not exist, it will be created and an empty repository will be 
initialized.  Otherwise an existing repository will be opened.  The call to 
:meth:`repo.root() <churro.Churro.root>` gets the root folder of the repository,
the starting point for traversing to any other objects in the repository.  From
there, adding data to the repository is as easy as instantiating data objects 
using folders as Python dicts.

Committing a Transaction
========================

So far no data has actually been stored yet.  You'll need to commit a 
transaction::

    import transaction

    transaction.commit()

.. note::

    If you're using `Pyramid <http://www.pylonsproject.org/>`_, you should avoid
    committing the transaction yourself and use
    `pyramid_tm <http://pypi.python.org/pypi/pyramid_tm>`_.  For other WSGI
    frameworks there is also `repoze.tm2
    <http://pypi.python.org/pypi/repoze.tm2>`_.

Persistent Properties
=====================

:class:`~churro.PersistentProperty` and its subclasses are responsible for 
serializing individual attributes of your Python objects to JSON.  
:class:`~churro.PersistentProperty` can handle values of any type natively
serializable to JSON.  These include strings, booleans, numbers, lists, and 
dictionaries.  Persistent properties can also hold as values other
:class:`~churro.Persistent` objects, allowing objects to be nested inside of
each other.  

Two additional property types, :class:`~churro.PersistentDate` and
:class:`~churro.PersistentDatetime` are included for storing `datetime.date` and
`datetime.datetime` objects respectively.  

For other types you'll need to provide a means for converting the type to
something serializable by JSON and then converting back to a Python object.
This is done by extending :class:`~churro.PersistentProperty` and overriding
the :meth:`~churro.PersistentProperty.to_json`,
:meth:`~churro.PersistentProperty.from_json`, and
:meth:`~churro.PersistentProperty.validate` methods.  The following is an
actual example from `Churro` code that illustrates this::

    import datetime

    class PersistentDate(PersistentProperty):

        def from_json(self, value):
            if value:
                return datetime.date(*map(int, value.split('-')))
            return value

        def to_json(self, value):
            if value:
                return '%s-%s-%s' % (value.year, value.month, value.day)
            return value

        def validate(self, value):
            if value is not None and not isinstance(value, datetime.date):
                raise ValueError("%s is not an instance of datetime.date")
            return value

You can use the new property type in your class definitions::

    class Contact(Persistent):
        name = PersistentProperty()
        address = PersistentProperty()
        birthday = PersistentDate()

        def __init__(self, name, address):
            self.name = name
            self.address = address

Mutable Property Values
=======================

`Churro` automatically keeps track of which objects have been mutated and saves
those objects at transaction commit time.  `Churro` does this by keeping track
of when a setter is called on a property and marking that object as `dirty`.  So
simply assigning a value to a property will cause that object to get persisted
at commit time::

    daniela.birthday = datetime.date(2010, 5, 12)

You can find yourself in a situation, however, where the assigned value is a 
mutable structure and instead of assigning a new value to the property you 
simply mutate the structure.  Let's say that we add a list of friends to our
`Contact` class::

    class Contact(Persistent):
        name = PersistentProperty()
        address = PersistentProperty()
        birthday = PersistentDate()
        friends = PersistentProperty()

        def __init__(self, name, address):
            self.name = name
            self.address = address
            self.friends = []

If we have a `Contact` instance that is `clean` and the only change we make is
to add a friend to the list, `Churro` will not detect the mutation and the 
change will not be persisted at commit time::

    # This change won't be persisted
    daniela.friends.append('Katy')

One way to get around this problem is to call the
:meth:`~churro.Persistent.set_dirty` method on the object that needs to be
saved::

    # Unless you call this method
    daniela.set_dirty()

This brute force method is always available, whatever you're doing.  `Churro`
does, however, provide helpers for the two most common types of mutable data,
dicts and lists.  These are :class:`~churro.PersistentDict` and
:class:`~churro.PersistentList` respectively.  We could rewrite the example
above to a use a :class:`~PersistentList` instead of a plain Python list::

    from churro import PersistentList
    
    class Contact(Persistent):
        name = PersistentProperty()
        address = PersistentProperty()
        birthday = PersistentDate()
        friends = PersistentProperty()

        def __init__(self, name, address):
            self.name = name
            self.address = address
            self.friends = PersistentList()

Now you don't need to call :meth:`~churro.Persistent.set_dirty` when adding a 
friend to a contact's friend list::

    # Don't need to call set_dirty, this change will be persisted
    daniela.friends.append('Silas')

API Reference
=============

.. automodule:: churro
 
  .. autoclass:: Churro
     :members:

  .. autoclass:: Persistent
     :members:
     
  .. autoclass:: PersistentFolder
     :members:

  .. autoclass:: PersistentDict
     :members:

  .. autoclass:: PersistentList
     :members:

  .. autoclass:: PersistentProperty
     :members:

  .. autoclass:: PersistentDate
     :members:

  .. autoclass:: PersistentDatetime
     :members:

