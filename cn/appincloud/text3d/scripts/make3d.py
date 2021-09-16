import argparse
import bpy
import math
from math import pi
import sys

def str2bool(str):
    return True if str.lower() == 'true' else False

def parse_args():
    """parsing and configuration"""
    desc = "3dtexts..."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-b', "--background", help="run at background", action="store_true")
    parser.add_argument('-P', type=str, default='')
    parser.add_argument('--text', type=str, default='hello', help='')
    parser.add_argument('--fontFamily', type=str, default='FreeSerif.ttf', help='')
    parser.add_argument('--extrude', type=float, default=0.2, help='')
    parser.add_argument('--fontSize', type=int, default=3, help='font size')
    parser.add_argument('--asSingleMesh', type=str2bool, default=True, help='as single mesh')
    return parser.parse_args()

#config=parse_args()
print(sys.argv)

def removeObjects( scn ):
    for ob in scn.objects:
        if (ob.type == 'FONT') or (ob.type == 'MESH'):
            bpy.context.collection.objects.unlink( ob )
 
scn = bpy.context.scene
removeObjects( scn )

#fnt = bpy.data.fonts.load('/home/terry/auto/fontfiles/GenJyuuGothic-Bold.ttf')
DEFAULT_FONT = "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"
#fnt = bpy.data.fonts.load(DEFAULT_FONT)

def text3d(text, fntFamily, fntSize, extrude, asSingleMesh=True):
	fnt = bpy.data.fonts.load(fntFamily)
	if asSingleMesh:
		makeobj(text, fnt, 'Text1', 0, fntSize, extrude)
	else:
		i = 0
		for t in text:
			name = "Text%d" % i
			makeobj(t, fnt, name, i, fntSize, extrude)
			i+=1

def makeobj(text, fnt, name = "Text1", offset = 0, size = 3, extrude = 0.2):
	# Create and name TextCurve object
	bpy.ops.object.text_add(
	location=(offset,0,0),
	rotation=(0,0,0))
	ob = bpy.context.object
	ob.name = name
	# TextCurve attributes
	ob.data.body = text
	ob.data.font = fnt
	ob.data.size = size
	# Inherited Curve attributes
	ob.data.extrude = extrude

	bpy.ops.object.convert(target='MESH', keep_original=False)

	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.uv.smart_project()
	bpy.ops.object.mode_set(mode='OBJECT')

n = 4
text = sys.argv[n]	 
fontFamily = sys.argv[n+1]
fontSize = int(sys.argv[n+2])
extrude = float(sys.argv[n+3])
asSingleMesh = str2bool(sys.argv[n+4])
filepath = sys.argv[n+5]
text3d(text, fontFamily, fontSize, extrude, asSingleMesh)
#text3d(config.text, config.fontFamily, config.fontSize, config.extrude, config.asSingleMesh)
#bpy.ops.export_scene.fbx(filepath="text.fbx")
bpy.ops.wm.usd_export(filepath=filepath)
