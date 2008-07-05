"""
The definition of different kinds of metadata that is put into the
mayavi registry
"""
# Author: Prabhu Ramachandran <prabhu@aero.iitb.ac.in>
# Copyright (c) 2008, Enthought, Inc.
# License: BSD Style.

# Enthought library imports.
from enthought.traits.api import HasTraits, Str, Callable, Either, List


################################################################################
# `Metadata` class.
################################################################################ 
class Metadata(HasTraits):
    """
    This class allows us to define metadata related to mayavi's sources,
    filters and modules.
    """
    
    # Our ID.
    id = Str

    # The class that implements the module/filter/source.
    class_name = Str

    # The factory that implements the object overrides the class_name if
    # not the empty string.  The callable will be given the filename to
    # open.
    factory = Either(Str, Callable, allow_none=False)

    # Description of the object being described.
    desc = Str

    # Help string for the object.
    help = Str

    # The name of this object in a menu. 
    menu_name = Str

    # The optional tooltip to display for this object.
    tooltip = Str

    ######################################################################
    # Metadata interface.
    ######################################################################
    def get_callable(self):
        """Return the callable that will create a new instance of the object implementing this
        metadata.
        """
        factory = self.factory
        if factory is not None:
            if callable(factory):
                symbol = factory
            elif isinstance(factory, str) and len(factory) > 0:
                symbol = self._import_symbol(factory)
            else:
                symbol = self._import_symbol(self.class_name)
        else:
            symbol = self._import_symbol(self.class_name)

        return symbol


    ######################################################################
    # Non-public interface.
    ######################################################################
    def _import_symbol(self, symbol_path):

        """ Import the symbol defined by the specified symbol path. 
        Copied from envisage's import manager.
        """

        if ':' in symbol_path:
            module_name, symbol_name = symbol_path.split(':')

            module = self._import_module(module_name)
            symbol = eval(symbol_name, module.__dict__)

        else:
            components = symbol_path.split('.')

            module_name = '.'.join(components[:-1])
            symbol_name = components[-1]

            module = __import__(
                module_name, globals(), locals(), [symbol_name]
            )

            symbol = getattr(module, symbol_name)

        # Event notification.
        self.symbol_imported = symbol

        return symbol
        

    def _import_module(self, module_name):

        """This imports the given module name.  This code is copied from
        envisage's import manager!

        """

        module = __import__(module_name)

        components = module_name.split('.')
        for component in components[1:]:
            module = getattr(module, component)

        return module


################################################################################
# `ModuleMetadata` class.
################################################################################ 
class ModuleMetadata(Metadata):
    pass

################################################################################
# `FilterMetadata` class.
################################################################################ 
class FilterMetadata(Metadata):
    pass

################################################################################
# `SourceMetadata` class.
################################################################################ 
class SourceMetadata(Metadata):

    # The file name extension that this reader/source handles.  Empty if
    # it does not read a file.
    extensions = List(Str)

    # Wildcard for the file dialog.
    wildcard = Str