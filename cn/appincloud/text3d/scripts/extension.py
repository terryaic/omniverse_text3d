import os
import asyncio
import carb
import carb.settings
from omni.kit.widget.settings import create_setting_widget, SettingType
import omni.kit.app
import omni.ext
import omni.ui
from pxr import UsdGeom, UsdShade, Vt, Gf, Sdf, Usd

WINDOW_NAME = "Make 3D Text"
EXTENSION_NAME = "Make 3D Text"
PY_PATH = os.path.dirname(os.path.realpath(__file__))
BLENDER_PATH = "cn.appincloud.text3d.blender_path"

class Extension(omni.ext.IExt):
    def __init__(self):
        self.num = 0
        self.enabled = True
        self.filepath = "tmptext.usd"
        self.extrude = 1.5
        self.fontsize = 20
        self.bevelDepth = 0
        self.text = "hello"
        self.singleMesh = True
        self._settings = carb.settings.get_settings()
        self._settings.set_default_string(BLENDER_PATH, "")
        self.load_fonts()

    def load_fonts(self):
        #self.fontfamily = "SourceHanSansCN.otf"
        #self.fonts = ["SourceHanSansCN.otf", "SourceHanSerifCN.otf"]
        self.fonts = []
        fontpath = os.path.join(PY_PATH, "fonts")
        for root, dir, files in os.walk(fontpath):
            for file in files:
                self.fonts.append(file)
        self.fontfamily = self.fonts[0]

    def on_startup(self, ext_id):
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=800, menu_path=f"{EXTENSION_NAME}")
        self._window.deferred_dock_in("Property")
        self._window.frame.set_build_fn(self._ui_rebuild)
        self._ui_rebuild()

    def on_shutdown(self):
        pass

    def copyMesh(self, obj, newObj):
        attributes = obj.GetAttributes()
        for attribute in attributes:
            attributeValue = attribute.Get()
            if attributeValue is not None:
                newAttribute = newObj.CreateAttribute(attribute.GetName(),attribute.GetTypeName(), False)
                newAttribute.Set(attributeValue)
        mesh = UsdGeom.Mesh(obj)
        newMesh = UsdGeom.Mesh(newObj)
        newMesh.SetNormalsInterpolation(mesh.GetNormalsInterpolation())

    async def generate_text(self):
        blender_path = self.getBlenderPath()
        import subprocess
        try:
            cmd = "%s -b -P %s/make3d.py %s %s %d %f %f %s %s" % (blender_path, PY_PATH, self.text, PY_PATH + "/fonts/" + self.fontfamily, self.fontsize, self.extrude, self.bevelDepth, self.singleMesh, self.filepath)
            carb.log_info(f"cmd:{cmd}")
            #p = subprocess.Popen(cmd, shell=False)
            args = [blender_path, "-b", "-P", os.path.join(PY_PATH, "make3d.py"), self.text, \
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
        stage2 = Usd.Stage.Open(self.filepath)
        selecteds = stage2.Traverse()
        carb.log_info(f"{selecteds}")
        for obj in selecteds:
            if obj.GetTypeName() == 'Xform':
                pass
            elif obj.GetTypeName() == "Mesh":
                newObj = stage1.DefinePrim(f"{path}/Text_{self.num}", "Mesh")
                self.copyMesh(obj, newObj)
                self.num += 1

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
                with omni.ui.VStack(spacing=2):
                    # intro
                    with omni.ui.CollapsableFrame(title="Description", height=10):
                        with omni.ui.VStack(style={"margin": 5}):
                            omni.ui.Label(
                                "This extension will generate 3d text with blender, please change the following path to your blender installed path",
                                word_wrap=True,
                            )
                    with omni.ui.HStack(height=20):
                        omni.ui.Label("blender installed path", word_wrap=True, width=omni.ui.Percent(35))
                        create_setting_widget(BLENDER_PATH, SettingType.STRING, width=omni.ui.Percent(55))
                        blender_button = omni.ui.Button("...", height=5, style={"padding": 12, "font_size": 20})
                        blender_button.set_clicked_fn(self._on_file_select_click)
                    with omni.ui.HStack(height=20):
                        omni.ui.Label("text", word_wrap=True, width=omni.ui.Percent(35))
                        text = omni.ui.StringField(height=10,  style={"padding": 5, "font_size": 20}).model
                        text.add_value_changed_fn(self.text_changed)
                        text.set_value(self.text)
                    with omni.ui.HStack(height=20):
                        omni.ui.Label("font", word_wrap=True, width=omni.ui.Percent(35))
                        fontFamily = omni.ui.ComboBox(0, *self.fonts, height=10, name="font family").model
                        fontFamily.add_item_changed_fn(self.combo_changed)
                    with omni.ui.HStack(height=20):
                        omni.ui.Label("font-size", word_wrap=True, width=omni.ui.Percent(35))
                        fontsize = omni.ui.IntField(height=10, style={"padding": 5, "font_size": 20}).model
                        fontsize.add_value_changed_fn(self.fontsize_changed)
                        fontsize.set_value(self.fontsize)
                    with omni.ui.HStack(height=20):
                        omni.ui.Label("extrude", word_wrap=True, width=omni.ui.Percent(35))
                        extrude = omni.ui.FloatField(height=10,  style={"padding": 5, "font_size": 20}).model
                        extrude.add_value_changed_fn(self.extrude_changed)
                        extrude.set_value(self.extrude)
                    with omni.ui.HStack(height=20):
                        omni.ui.Label("bevel depth", word_wrap=True, width=omni.ui.Percent(35))
                        bevel = omni.ui.FloatField(height=10,  style={"padding": 5, "font_size": 20}).model
                        bevel.add_value_changed_fn(self.beveldepth_changed)
                        bevel.set_value(self.bevelDepth)
                    with omni.ui.HStack(height=20):
                        omni.ui.Label("as a single mesh", word_wrap=True, width=omni.ui.Percent(35))
                        singleMesh = omni.ui.CheckBox(height=10,  style={"padding": 5, "font_size": 20}).model
                        singleMesh.add_value_changed_fn(self.singleMesh_changed)
                        singleMesh.set_value(self.singleMesh)
                    with omni.ui.HStack(height=20):
                        button = omni.ui.Button("Generate 3D Text", height=5, style={"padding": 12, "font_size": 20})
                        button.set_clicked_fn(lambda: asyncio.ensure_future(self.generate_text()))

    def getBlenderPath(self):
        s = self._settings.get(BLENDER_PATH)
        return s

    def _on_filepicker_cancel(self, *args):
        self._filepicker.hide()
        
    def _on_filter_item(self, item):
        return True

    async def _on_selection(self, filename, dirname):
        path = os.path.join(dirname,filename)
        if os.path.isfile(path):
            pass
        else:
            path = os.path.join(path, "blender")
        self._settings.set(BLENDER_PATH, path)
        self._filepicker.hide()
        self._window.frame.rebuild()
        
    def _on_file_select_click(self):
        self._filepicker = omni.kit.window.filepicker.FilePickerDialog(
            f"{EXTENSION_NAME}/Select Blender installed path",
            click_apply_handler=lambda f, d: asyncio.ensure_future(self._on_selection(f, d)),
            click_cancel_handler= self._on_filepicker_cancel,
            item_filter_options= ["*"],
            item_filter_fn=self._on_filter_item,
        )