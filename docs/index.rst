Welcome to PROCSIM Running/Results Frontend's documentation!
============================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
* :ref:`Note on optimisation methods <note-anchor>`

Modules
=======

.. automodule:: Main
   :members:

.. automodule:: Home
   :members:

.. automodule:: ECSimulator
   :members:

.. automodule:: ECOptimizer
   :members:

.. automodule:: Help
   :members:

.. automodule:: Settings
   :members:

.. automodule:: SimMenu
   :members:

.. automodule:: OptimMenu
   :members:

.. automodule:: ResultScreen
   :members:

.. automodule:: ClickableGraph
   :members:

.. automodule:: ProcsimGraphs
   :members:

.. automodule:: GraphParamSelector
   :members:

.. automodule:: ProcsimRun
   :members:

.. The util module is not showing because it only has a class with static methods, but adding it makes it appear in the index
.. automodule:: Util

.. autoclass:: Util.Util
   :members:

.. _note-anchor:

Note on optimisation methods
============================

* By accessing Settings.Settings.optimizationNames() most of the application's needs are met
* Buttons labels and other elements are dynamically created by reading the above tuple and using the names and indeces inside
* To add PROCSIM's functionality to these elements ProcsimRun.ProcsimRun.cmExecute() must be updated to contain the procedure related to the correspondent method