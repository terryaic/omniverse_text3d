import os
import math
import asyncio

import carb
import carb.settings

import omni.kit.app
import omni.ext
import omni.ui
import omni.kit.ui_windowmanager
import omni.appwindow

from pxr import UsdGeom, UsdShade, Vt, Gf, Sdf, Usd

try:
    import omni.kit.renderer
    import omni.kit.imgui_renderer

    standalone_renderer_present = True
except:
    standalone_renderer_present = False


WINDOW_NAME = "Make 3D Text"
EXTENSION_NAME = "Make 3D Text"
PY_PATH = os.path.dirname(os.path.realpath(__file__))
BLENDER_PATH = "C:/Users/terry/AppData/Local/ov/pkg/blender-3.0.0-usd.100.1.3/Release"


class Extension(omni.ext.IExt):
    def __init__(self):
        self.loads()
        self.num = 0
        self.enabled = True
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=800, menu_path=f"{EXTENSION_NAME}")
        self._scroll_frame = omni.ui.ScrollingFrame()
        self._ui_rebuild()
        self._window.frame.set_build_fn(self._ui_rebuild)

    def loads(self):
        self.blender_path = BLENDER_PATH
        self.filepath = "tmptext.usd"
        self.extrude = 1.5
        self.fontsize = 20
        self.bevelDepth = 0
        self.text = "hello"
        self.singleMesh = True
        #self.fontfamily = "SourceHanSansCN.otf"
        #self.fonts = ["SourceHanSansCN.otf", "SourceHanSerifCN.otf"]
        self.fonts = []
        fontpath = os.path.join(PY_PATH, "fonts")
        for root, dir, files in os.walk(fontpath):
            for file in files:
                self.fonts.append(file)
        self.fontfamily = self.fonts[0]

    def get_name(self):
        return EXTENSION_NAME

    def on_startup(self, ext_id):
        stage = omni.usd.get_context().get_stage()
        self._context = omni.usd.get_context()
        self.event_sub = self._context.get_stage_event_stream().create_subscription_to_pop(self._on_event)
        self._timeline_iface = omni.timeline.get_timeline_interface()
        self._timeline_events = self._timeline_iface.get_timeline_event_stream().create_subscription_to_pop(
            self._on_timeline_event
        )
        self.update_events = (
            omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(self._on_update)
        )

    def on_shutdown(self):
        pass

    def _on_event(self, e):
        if e.type == int(omni.usd.StageEventType.SELECTION_CHANGED):
            pass
        elif e.type == int(omni.usd.StageEventType.OPENED) or e.type == int(omni.usd.StageEventType.ASSETS_LOADED):
            pass

    def _on_timeline_event(self, e):
        stage = omni.usd.get_context().get_stage()
        if e.type == int(omni.timeline.TimelineEventType.PLAY):
            pass
        elif e.type == int(omni.timeline.TimelineEventType.STOP):
            pass
        elif e.type == int(omni.timeline.TimelineEventType.PAUSE):
            pass

    def _on_update(self, dt):
        pass

    def copyMesh(self, obj, newObj):
        attributes = obj.GetAttributes()
        #carb.log_info(f"attributes:{attributes}")
        for attribute in attributes:
            attributeValue = attribute.Get()
            if attributeValue is not None:
                newAttribute = newObj.CreateAttribute(attribute.GetName(),attribute.GetTypeName(), False)
                newAttribute.Set(attributeValue)
        mesh = UsdGeom.Mesh(obj)
        newMesh = UsdGeom.Mesh(newObj)
        newMesh.SetNormalsInterpolation(mesh.GetNormalsInterpolation())

    async def generate_text(self):
        import subprocess
        try:
            cmd = "%s/blender -b -P %s/make3d.py %s %s %d %f %f %s %s" % (self.blender_path, PY_PATH, self.text, PY_PATH + "/fonts/" + self.fontfamily, self.fontsize, self.extrude, self.bevelDepth, self.singleMesh, self.filepath)
            carb.log_info(f"cmd:{cmd}")
            #p = subprocess.Popen(cmd, shell=False)
            args = [os.path.join(self.blender_path, "blender"), "-b", "-P", os.path.join(PY_PATH, "make3d.py"), self.text, \
            os.path.join(PY_PATH, "fonts", self.fontfamily), str(self.fontsize), str(self.extrude), str(self.bevelDepth), str(self.singleMesh), self.filepath]
            p = subprocess.Popen(args, shell=False)
            p.wait()
        except Exception as e:
            print(e)
        stage1 = omni.usd.get_context().get_stage()
        selected_paths = omni.usd.get_context().get_selection().get_selected_prim_paths()
        defaultPrimPath = str(stage1.GetDefaultPrim().GetPath())
        if len(selected_paths) > 0:
            path = selected_paths[0]
        else:
            path = defaultPrimPath
        stage = Usd.Stage.Open(self.filepath)
        selecteds = stage.Traverse()
        carb.log_info(f"{selecteds}")
        for obj in selecteds:
            if obj.GetTypeName() == 'Xform':
                #carb.log_info(f"ignore xform:{obj}")
                pass
            elif obj.GetTypeName() == "Mesh":
                newObj = stage1.DefinePrim(f"{path}/Text_{self.num}", "Mesh")
                self.copyMesh(obj, newObj)
                self.num += 1
            else:
                #carb.log_info(f"ignore other:{obj}")
                pass

    def fontsize_changed(self, text_model):
        self.fontsize = text_model.get_value_as_int()
        carb.log_info(f"fontsize changed:{self.fontsize}")

    def extrude_changed(self, text_model):
        self.extrude = text_model.get_value_as_float()
        carb.log_info(f"extrude changed:{self.extrude}")

    def beveldepth_changed(self, text_model):
        self.bevelDepth = text_model.get_value_as_float()
        carb.log_info(f"extrude changed:{self.bevelDepth}")

    def text_changed(self, text_model):
        self.text = text_model.get_value_as_string()
        carb.log_info(f"text changed:{self.text}")

    def blenderpath_changed(self, text_model):
        self.blender_path = text_model.get_value_as_string()
        carb.log_info(f"text2 changed:{self.blender_path}")

    def combo_changed(self, combo_model, item):
            all_options = [
                combo_model.get_item_value_model(child).as_string
                for child in combo_model.get_item_children()
            ]
            current_index = combo_model.get_item_value_model().as_int
            self.fontfamily = all_options[current_index]
            carb.log_info(f"font changed to: {self.fontfamily}")
        
    def singleMesh_changed(self, model):
        self.singleMesh = model.get_value_as_bool()
        carb.log_info(f"singleMesh changed:{self.singleMesh}")

    def _ui_rebuild(self):
        self._scroll_frame = omni.ui.ScrollingFrame()
        with self._window.frame:
            with self._scroll_frame:
                with omni.ui.VStack(spacing=5):
                    # intro
                    with omni.ui.CollapsableFrame(title="Description", height=10):
                        with omni.ui.VStack(style={"margin": 5}):
                            omni.ui.Label(
                                "This extension will generate 3d text with blender, please change the following path to your blender installed path",
                                word_wrap=True,
                            )

                    with omni.ui.HStack():
                        omni.ui.Label("blender installed path", height=10)
                        blender_path = omni.ui.StringField(height=10,  style={"padding": 5, "font_size": 20}).model
                        blender_path.add_value_changed_fn(self.blenderpath_changed)
                        blender_path.set_value(self.blender_path)

                    with omni.ui.HStack():
                        omni.ui.Label("text", height=10)
                        text = omni.ui.StringField(height=10,  style={"padding": 5, "font_size": 20}).model
                        text.add_value_changed_fn(self.text_changed)
                        text.set_value(self.text)

                    with omni.ui.HStack():
                        omni.ui.Label("font", height=10)
                        fontFamily = omni.ui.ComboBox(0, *self.fonts, height=10, name="font family").model
                        fontFamily.add_item_changed_fn(self.combo_changed)

                    with omni.ui.HStack():
                        omni.ui.Label("font-size", height=10)
                        fontsize = omni.ui.IntField(height=10, style={"padding": 5, "font_size": 20}).model
                        fontsize.add_value_changed_fn(self.fontsize_changed)
                        fontsize.set_value(self.fontsize)

                    with omni.ui.HStack():
                        omni.ui.Label("extrude", height=10)
                        extrude = omni.ui.FloatField(height=10,  style={"padding": 5, "font_size": 20}).model
                        extrude.add_value_changed_fn(self.extrude_changed)
                        extrude.set_value(self.extrude)

                    with omni.ui.HStack():
                        omni.ui.Label("bevel depth", height=10)
                        bevel = omni.ui.FloatField(height=10,  style={"padding": 5, "font_size": 20}).model
                        bevel.add_value_changed_fn(self.beveldepth_changed)
                        bevel.set_value(self.bevelDepth)

                    with omni.ui.HStack():
                        omni.ui.Label("as a single mesh", height=10)
                        singleMesh = omni.ui.CheckBox(height=10,  style={"padding": 5, "font_size": 20}).model
                        singleMesh.add_value_changed_fn(self.singleMesh_changed)
                        singleMesh.set_value(self.singleMesh)
                    
                    with omni.ui.HStack():
                        button = omni.ui.Button("Generate 3D Text", height=5, style={"padding": 12, "font_size": 20})
                        button.set_clicked_fn(lambda: asyncio.ensure_future(self.generate_text()))
