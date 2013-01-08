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

Contents
========

.. toctree::
    :maxdepth: 2

    quickstart
    properties
    api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
