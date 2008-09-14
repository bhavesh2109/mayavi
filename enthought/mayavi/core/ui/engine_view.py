"""The MayaVi view in Envisage.

"""
# Author: Prabhu Ramachandran <prabhu_r@users.sf.net>
# Copyright (c) 2005-2008, Enthought, Inc.
# License: BSD Style.

# Standard library imports.
from os.path import join

# Enthought library imports.
from enthought.traits.api import Instance, HasTraits, Any, Delegate
from enthought.traits.ui.api import (Group, Item, TreeEditor, TreeNode,
        ObjectTreeNode, View, Handler, UIInfo)
from enthought.traits.ui.menu import ToolBar, Action, Separator
from enthought.resource.resource_path import resource_path
from enthought.pyface.image_resource import ImageResource

# Local imports.
from enthought.mayavi.core.engine import Engine
from enthought.mayavi.core.base import Base
from enthought.mayavi.core.adder_node import ModuleFilterAdderNode, \
        SourceAdderNode, ModuleAdderNode, FilterAdderNode, \
        SceneAdderNode, AdderNode
from enthought.mayavi.action.help import open_help_index
from enthought.mayavi.core.recorder import start_recording, stop_recording

class EngineViewHandler(Handler):
    """ A handler for the EngineView object. 
    """

    info = Instance(UIInfo)

    def init_info(self, info):
        """ Informs the handler what the UIInfo object for a View will be.
        Overridden here to save a reference to the info object.
        
        """
        self.info = info
        return

    def _on_dclick(self, object):
        """ Called when a node in the tree editor is double-clicked.
        """
        if isinstance(object, SceneAdderNode):
            self.info.object._perform_new_scene()
        else:
            object.edit_traits(view=object.dialog_view(), 
                           parent=self.info.ui.control )

    def _on_select(self, object):
        """ Called when a node in the tree editor is selected.
        """
        self.info.object.engine._on_select(object)


class AdderTreeNode(TreeNode):
    """ TreeNode for the adder nodes.
    """

    children=''
    label='label'
    auto_open=True
    copy=False
    delete_me=False
    rename_me=False
    tooltip='tooltip'
    icon_path=resource_path()
    icon_item='add.ico'
 

##############################################################################
# EngineView class.
##############################################################################
class EngineView(HasTraits):
    """ A view displaying the engine's object tree. """

    # The MayaVi engine we are a view of.
    engine = Instance(Engine, allow_none=True)
   
    # Path used to search for images
    _image_path = [join(resource_path(), 'images'), ]

    # The icon of the dialog
    icon = ImageResource('mv2.ico', search_path=_image_path)

    # Nodes on the tree.
    nodes = Any

    # Toolbar
    toolbar = Instance(ToolBar)

    # Some delegates, for the toolbar to update
    scenes = Delegate('engine')
    current_selection = Delegate('engine')

    ###########################################################################
    # `object` interface.
    ###########################################################################
    def __init__(self, **traits):
        super(EngineView, self).__init__(**traits)

                
    ###########################################################################
    # `HasTraits` interface.
    ###########################################################################
    def default_traits_view(self):
        """The default traits view of the Engine View.
        """
        
        tree_editor = TreeEditor(editable=False,
                                 hide_root=True,
                                 on_dclick='handler._on_dclick',
                                 on_select='handler._on_select',
                                 orientation='vertical',
                                 selected='object.engine.current_selection',
                                 nodes=self.nodes
                                 )


        view = View(Group(Item(name='engine',
                               id='engine',
                               editor=tree_editor,
                               resizable=True ),
                          show_labels=False,
                          show_border=False,
                          orientation='vertical'),
                    id='enthought.mayavi.engine',
                    help=False,
                    resizable=True,
                    undo=False,
                    revert=False,
                    ok=False,
                    cancel=False,
                    title='Mayavi pipeline',
                    icon=self.icon,
                    width=0.3,
                    height=0.3,
                    toolbar=self.toolbar,
                    handler = EngineViewHandler)
        return view
    

    def _nodes_default(self):
        """ The default value of the cached nodes list.
        """
        # Now setup the view.
        nodes = [TreeNode(node_for=[Engine],
                          children='children_ui_list',
                          label='=Mayavi',
                          auto_open=False,
                          copy=False,
                          delete=False,
                          rename=False,
                          ),
                 ObjectTreeNode(node_for=[Base],
                                children='children_ui_list',
                                label='name',
                                auto_open=True,
                                copy=True,
                                delete=True,
                                rename=True,
                                tooltip='=Right click for more options',
                                ),
                 AdderTreeNode(node_for=[SceneAdderNode],
                               icon_item='add_scene.png',
                               ),
                 AdderTreeNode(node_for=[SourceAdderNode],
                               icon_item='add_source.png',
                               ),
                 AdderTreeNode(node_for=[ModuleFilterAdderNode],
                               icon_item='add_module.png',
                               ),
                 ]
        return nodes


    def _toolbar_default(self): 
        add_scene = \
            Action(
                image=ImageResource('add_scene.png',
                                            search_path=self._image_path),
                tooltip="Create a new scene",
                defined_when='True',
                enabled_when='True',
                perform=self._perform_new_scene,
            )

        add_source = \
            Action(
                image=ImageResource('add_source.png',
                                            search_path=self._image_path),
                tooltip="Add a data source",
                defined_when='True',
                enabled_when='len(scenes) > 0',
                perform=self._perform_add_source,
            )
            
        add_module = \
            Action(
                image=ImageResource('add_module.png',
                                            search_path=self._image_path),
                tooltip="Add a visualization module",
                defined_when='True',
                # isinstance doesn't work in enabled_when
                enabled_when=\
                    'current_selection is not None and'
                    '( hasattr(current_selection, "output_info")'
                    'or current_selection.__class__.__name__ =='
                    '"ModuleFilterAdderNode")',
                perform=self._perform_add_module,
            )

        add_filter = \
            Action(
                image=ImageResource('add_filter.png',
                                            search_path=self._image_path),
                tooltip="Add a processing filter",
                defined_when='True',
                enabled_when=\
                    'current_selection is not None and'
                    '( hasattr(current_selection, "output_info")'
                    'or current_selection.__class__.__name__ =='
                    '"ModuleFilterAdderNode")',
                perform=self._perform_add_filter,
             )

        help = \
            Action(
                image=ImageResource('help-action.png',
                                            search_path=self._image_path),
                tooltip="Help on the Mayavi pipeline",
                defined_when='True',
                enabled_when='True',
                perform=open_help_index,
            )
        record = \
            Action(
                image=ImageResource('record.png',
                                     search_path=self._image_path),
                tooltip="Start/Stop script recording",
                style='toggle',
                checked=False,
                defined_when='True',
                enabled_when='engine is not None',
                perform=self._perform_record,
            )

        return ToolBar(
            add_scene,
            add_source,
            add_module,
            add_filter,
            Separator(),
            help,
            record,
            image_size = (16, 16),
            show_tool_names = False,
            show_divider = False,
        )


    ###########################################################################
    # private interface.
    ###########################################################################

    def _perform_new_scene(self):
        self.engine.new_scene()
        self.engine.current_selection = self.engine.current_scene

    def _perform_add_source(self):
        adder = SourceAdderNode(object=self.engine.current_scene)
        adder.edit_traits(view=adder.dialog_view())


    def _perform_add_module(self):
        object = self.engine.current_selection
        if isinstance(object, AdderNode):
            object = object.object
        adder = ModuleAdderNode(object=object)
        adder.edit_traits(view=adder.dialog_view())


    def _perform_add_filter(self):
        object = self.engine.current_selection
        if isinstance(object, AdderNode):
            object = object.object
        adder = FilterAdderNode(object=object)
        adder.edit_traits(view=adder.dialog_view())

    def _perform_record(self):
        e = self.engine
        if e.recorder is None:
            start_recording(e, known=True, script_id='engine')
        else:
            stop_recording(e)


### EOF ######################################################################
