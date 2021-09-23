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
import numpy as np

from pxr import UsdGeom, UsdShade, Vt, Gf, Sdf, Usd

try:
    import omni.kit.renderer
    import omni.kit.imgui_renderer

    standalone_renderer_present = True
except:
    standalone_renderer_present = False


WINDOW_NAME = "Make 3D Text"
EXTENSION_NAME = "Make 3D Text"
BLENDER_PATH = "C:/Users/terry/AppData/Local/ov/pkg/blender-3.0.0-usd.100.1.3/Release"


class Extension(omni.ext.IExt):
    def __init__(self):
        self.enabled = True
        self._window = omni.ui.Window(EXTENSION_NAME, width=600, height=800, menu_path=f"{EXTENSION_NAME}")
        self._scroll_frame = omni.ui.ScrollingFrame()
        self._ui_rebuild()
        self._window.frame.set_build_fn(self._ui_rebuild)
        self.loads()

    def loads(self):
        self.blender_path = BLENDER_PATH
        self.filepath = "C:/Users/terry/Downloads/text.usd"
        self.extrude = 0.2
        self.fontsize = 3
        self.text = "hello"
        self.fontfamily = "SourceHanSansCN.otf"

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
            self.loads()

    def _on_timeline_event(self, e):
        stage = omni.usd.get_context().get_stage()
        if e.type == int(omni.timeline.TimelineEventType.PLAY):
            # Disable visualization dropdown
            # Change button to Stop
            pass
        elif e.type == int(omni.timeline.TimelineEventType.STOP):
            # Enable visualization dropdown
            # Change button to Drive
            carb.log_info("stoped")
        elif e.type == int(omni.timeline.TimelineEventType.PAUSE):
            # Change button to Drive
            pass

    def _on_update(self, dt):
        pass

    def copyMesh(self, obj, newObj):
                attributes = obj.GetAttributes()
                carb.log_info(f"attributes:{attributes}")
                for attribute in attributes:
                    attributeValue = attribute.Get()
                    carb.log_info(f"attribute:{attribute}")
                    carb.log_info(f"attributeValue:{attributeValue}")
                    if attributeValue is not None:
                        newAttribute = newObj.CreateAttribute(attribute.GetName(),attribute.GetTypeName(), False)
                        newAttribute.Set(attributeValue)
                        #carb.log_info(f"help:{help(attribute.GetVariability())}")'faceVarying'
                #carb.log_info(f"properties:{obj.GetProperties()}")
                mesh = UsdGeom.Mesh(obj)
                carb.log_info(f"allv:{mesh.GetNormalsInterpolation()}")
                newMesh = UsdGeom.Mesh(newObj)
                newMesh.SetNormalsInterpolation(mesh.GetNormalsInterpolation())

    async def test(self):
        import subprocess
        PY_PATH = os.path.dirname(os.path.realpath(__file__))
        #PY_PATH = "C:/Users/terry/AppData/Local/ov/pkg/create-2021.3.3/kit/exts/cn.appincloud.text3d/cn/appincloud/text3d/scripts"
        #FONT_PATH = "C:/Users/terry/AppData/Local/ov/pkg/create-2021.3.3/kit/exts/cn.appincloud.text3d/fonts"
        cmd = "%s/blender -b -P %s/make3d.py %s %s %d %f %s %s" % (self.blender_path, PY_PATH, self.text, PY_PATH + "/fonts/" + self.fontfamily, self.fontsize, self.extrude, True, self.filepath)
        carb.log_info(f"cmd:{cmd}")
        p = subprocess.Popen(cmd, shell=False)
        p.wait()
        stage1 = omni.usd.get_context().get_stage()
        prim = stage1.GetPrimAtPath("/World")
        stage = Usd.Stage.Open(self.filepath)
        #carb.log_info(f"stage:{help(stage)}")
        selecteds = stage.Traverse()
        carb.log_info(f"{selecteds}")
        for obj in selecteds:
            if obj.GetTypeName() == 'Xform':
                carb.log_info(f"ignore xform:{obj}")
            elif obj.GetTypeName() == "Mesh":
                newObj = stage1.DefinePrim(f"/World/{obj.GetName()}", "Mesh")
                self.copyMesh(obj, newObj)
            else:
                carb.log_info(f"ignore other:{obj}")

    #split the subset, not working yet.
    def doSplit(self, selected):
        stage = omni.usd.get_context().get_stage()
        if selected.GetTypeName() != 'Mesh':
            return
        name = selected.GetName()
        points = selected.GetAttribute("points").Get()
        faceVertexIndices = selected.GetAttribute("faceVertexIndices").Get()
        carb.log_info(f"faceVertexIndices:{faceVertexIndices}")
        faceVertexIndices = np.array(faceVertexIndices).reshape(int(len(faceVertexIndices)/4),4)
        normals = selected.GetAttribute("normals").Get()
        carb.log_info(f"normals:{normals}")
        for child in selected.GetAllChildren():
            subsetName = child.GetName()
            indices = child.GetAttribute("indices").Get()
            points1 = points
            #payload1 = Usd.Stage.CreateNew("payload1.usd")
            payload1 = stage.DefinePrim("/payload1", "Xform")
            mesh = stage.DefinePrim(f"/payload1/{name}_{subsetName}", "Mesh")
            path = f"/payload1/{name}_{subsetName}"
            mesh = UsdGeom.Mesh.Get(stage, path)
            mesh.CreatePointsAttr().Set(points1)
            newVertexIndices = []
            newNormals = []
            count = 0
            for index in faceVertexIndices:
                toAdd = 4
                for i in index:
                    if i not in indices:
                        #carb.log_info(f"{i} not in index")
                        toAdd -= 1
                if toAdd > 0:
                    newVertexIndices.append(index)
                    newNormals.append(normals[count*4])
                    newNormals.append(normals[count*4+1])
                    newNormals.append(normals[count*4+2])
                    newNormals.append(normals[count*4+3])
                count += 1
            faceCounts = [4]*len(newVertexIndices)
            newVertexIndices = np.array(newVertexIndices).reshape(len(newVertexIndices)*4)
            carb.log_info(f"newVertexIndices:{len(newVertexIndices)}")
            mesh.CreateFaceVertexCountsAttr().Set(faceCounts)
            mesh.CreateFaceVertexIndicesAttr().Set(newVertexIndices)
            mesh.CreateNormalsAttr().Set(newNormals)

    #center the selected object
    async def doCenter(self):
        stage = omni.usd.get_context().get_stage()
        selected_paths = omni.usd.get_context().get_selection().get_selected_prim_paths()
        carb.log_info(f"{selected_paths}")
        for selected_path in selected_paths:
            selected = stage.GetPrimAtPath(selected_path)
            carb.log_info(f"selected:{help(selected)}")
            if selected.GetTypeName() == 'Xform':
                carb.log_info(f"children:{selected.GetAllChildren()}")
                for child in selected.GetAllChildren():
                    self.doCenterPrim(child)
            else:
                self.doCenterPrim(selected)

    async def doCenterAll(self):
        stage = omni.usd.get_context().get_stage()
        selecteds = stage.Traverse()#omni.usd.get_context().get_selection().get_selected_prim_paths()
        carb.log_info(f"{selecteds}")
        for selected in selecteds:
            if selected.GetTypeName() == 'Xform':
                continue
            else:
                self.doCenterPrim(selected)

    def doCenterPrim(self, selected):
        points = selected.GetAttribute("points").Get()
        carb.log_info(f"points:{points}")
        if points is None:
            return
        ps = np.array(points)
        psmean = ps.mean(axis=0)
        carb.log_info(f"mean:{psmean}")
        ps[:] -= psmean
        selected.GetAttribute("points").Set(ps)

        scale = [1,1,1]#actually, scale is not used!
        if selected.HasAttribute("xformOp:translate"):
            attr_position = selected.GetAttribute("xformOp:translate")
            if selected.HasAttribute("xformOp:scale"):
                scale = selected.GetAttribute("xformOp:scale").Get()
        else:
            attr_position = selected.GetParent().GetAttribute("xformOp:translate")
            if selected.GetParent().GetAttribute("xformOp:scale").Get() is not None:
                scale = selected.GetParent().GetAttribute("xformOp:scale").Get()
        carb.log_info(f"attr_position:{attr_position} attr_scale:{scale}")
        translate = attr_position.Get()
        if translate is not None:
            carb.log_info(f"get translate:{translate}")
            #attr_position = selected.CreateAttribute("xformOp:translate", Sdf.ValueTypeNames.Double3, False)
            newtranslate = Gf.Vec3d(0,0,0)
            newtranslate[0] = translate[0] + psmean[0]
            newtranslate[1] = translate[1] + psmean[1]
            newtranslate[2] = translate[2] + psmean[2]
            attr_position.Set(newtranslate)
            carb.log_info(f"set translate:{newtranslate}")
        else:
            attr_position = selected.CreateAttribute("xformOp:translate", Sdf.ValueTypeNames.Double3, False)
            carb.log_info(f"create translate:{attr_position}")
            translate = Gf.Vec3d(0,0,0)
            translate[0] += psmean[0]
            translate[1] += psmean[1]
            translate[2] += psmean[2]
            attr_position = selected.GetAttribute("xformOp:translate")
            attr_position.Set(translate)

        self._window.frame.rebuild()

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

    def _ui_rebuild(self):
        self._scroll_frame = omni.ui.ScrollingFrame()
        with self._window.frame:
            with self._scroll_frame:
                with omni.ui.VStack(spacing=5):
                    # intro
                    with omni.ui.CollapsableFrame(title="Description", height=10):
                        with omni.ui.VStack(style={"margin": 5}):
                            omni.ui.Label(
                                "This extension will center the selected object",
                                word_wrap=True,
                            )
                    omni.ui.Label("blender installed path:", height=10)
                    strText2 = omni.ui.StringField(height=10,  style={"padding": 12, "font_size": 20}).model
                    strText2.add_value_changed_fn(self.blenderpath_changed)

                    omni.ui.Label("text:", height=10)
                    strText = omni.ui.StringField(height=10,  style={"padding": 12, "font_size": 20}).model
                    strText.add_value_changed_fn(self.text_changed)

                    fontFamily = omni.ui.ComboBox(0, "SourceHanSansCN.otf", "SourceHanSerifCN.otf", height=10, name="font family").model
                    fontFamily.add_item_changed_fn(self.combo_changed)
                    
                    # Test Drive/Reset Button
                    with omni.ui.HStack():
                        button_label3 = (
                            "test"
                        )
                        button3 = omni.ui.Button(button_label3, height=5, style={"padding": 12, "font_size": 20})
                        button3.set_clicked_fn(lambda: asyncio.ensure_future(self.test()))