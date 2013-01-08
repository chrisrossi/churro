=======================
Getting Started Quickly
=======================

You can use `Churro` if you only read this page.  Some topics are covered 
more thoroughly later, but thorough discussion is not required to start using
`Churro` now.  

Defining Persistent Types
-------------------------

In order for an object to be saved in a `Churro` repository, it must inherit 
from :class:`Persistent <churro.Persistent>` or 
:class:`PersistentFolder <churro.PersistentFolder>`.  Attributes of your 
persistent objects that you want to be persisted must be derived from 
:class:`PersistentProperty`.  Probably the best way to illustrate is by 
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
--------------------------------

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
------------------------

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
