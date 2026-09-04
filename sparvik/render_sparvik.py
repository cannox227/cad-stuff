import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import sparvik

import numpy as np
import trimesh
import pyrender
from PIL import Image

out = ROOT / "sparvik_render.png"
scene=pyrender.Scene(bg_color=[0.93,0.91,0.87,1], ambient_light=[0.32,0.30,0.28])
def mat(color, rough=.45, metal=0): return pyrender.MetallicRoughnessMaterial(baseColorFactor=[*color,1],roughnessFactor=rough,metallicFactor=metal)
def add(mesh, material):
    scene.add(pyrender.Mesh.from_trimesh(mesh, material=material))


def add_cover(path, center, width=92, height=300, rotation_degrees=-20):
    """Put a real album-cover image on a thin, tilted sleeve."""
    image = np.asarray(Image.open(path).convert("RGB"))
    vertices = np.array([
        [-width / 2, 0, -height / 2],
        [ width / 2, 0, -height / 2],
        [ width / 2, 0,  height / 2],
        [-width / 2, 0,  height / 2],
    ], dtype=float)
    faces = np.array([[0, 1, 2], [0, 2, 3]])
    uv = np.array([[0, 1], [1, 1], [1, 0], [0, 0]], dtype=float)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    mesh.visual = trimesh.visual.texture.TextureVisuals(uv=uv, image=image)
    mesh.apply_transform(trimesh.transformations.rotation_matrix(
        np.deg2rad(rotation_degrees), [0, 1, 0]
    ))
    mesh.apply_translation(center)
    scene.add(pyrender.Mesh.from_trimesh(mesh, smooth=False))


def add_textured_asset(path, target_extents, center, rotation_degrees=0):
    """Load a downloaded GLB, rescale it, rotate it, and preserve materials."""
    asset = trimesh.load(path, force="scene").dump(concatenate=True)
    asset.apply_scale(np.asarray(target_extents) / asset.extents)
    asset.apply_translation(np.asarray(center) - asset.bounds.mean(axis=0))
    if rotation_degrees:
        # Rotate around Y so the upright sleeves lean in X/Z, toward the
        # cabinet's left wall. A negative angle moves their tops left.
        pivot = np.asarray(center) - np.array([0, 0, target_extents[2] / 2])
        asset.apply_transform(
            trimesh.transformations.rotation_matrix(
                np.deg2rad(rotation_degrees), [0, 1, 0], point=pivot
            )
        )
    scene.add(pyrender.Mesh.from_trimesh(asset))


def box(ext, pos, material):
    mesh = trimesh.creation.box(extents=ext)
    mesh.apply_translation(pos)
    add(mesh, material)


def plant_leaf(position, scale, rotation, material):
    """Add a simple 3D Coleus scutellarioides leaf."""
    leaf = trimesh.creation.icosphere(subdivisions=2, radius=1)
    leaf.apply_scale(scale)
    leaf.apply_transform(trimesh.transformations.euler_matrix(*rotation))
    leaf.apply_translation(position)
    add(leaf, material)


def add_coleus():
    """Add a colorful potted Coleus scutellarioides on top of the cabinet."""
    pot = mat([.18, .08, .045], .72)
    stem = mat([.12, .22, .07], .8)
    leaf_green = mat([.12, .34, .12], .72)
    leaf_red = mat([.48, .08, .08], .68)
    leaf_purple = mat([.25, .08, .25], .7)

    # Cabinet top is z=1260 mm. Pot and plant are scaled for the render only.
    box((90, 90, 75), (420, -220, 1297.5), pot)
    for x, y, top in [(420, -220, 1500), (405, -220, 1460), (435, -220, 1475)]:
        stem_mesh = trimesh.creation.cylinder(radius=4, height=top - 1335, sections=16)
        stem_mesh.apply_translation((x, y, (top + 1335) / 2))
        add(stem_mesh, stem)

    leaves = [
        ((375, -220, 1460), (42, 10, 26), (0.0, 0.35, -0.25), leaf_red),
        ((465, -220, 1475), (44, 10, 28), (0.0, -0.4, 0.2), leaf_green),
        ((395, -220, 1510), (38, 10, 24), (0.0, 0.15, 0.55), leaf_purple),
        ((445, -220, 1535), (43, 10, 28), (0.0, -0.25, -0.45), leaf_red),
        ((420, -220, 1565), (36, 10, 24), (0.0, 0.0, 0.0), leaf_green),
        ((365, -220, 1515), (34, 10, 23), (0.0, 0.6, -0.5), leaf_green),
    ]
    for position, scale, rotation, material in leaves:
        plant_leaf(position, scale, rotation, material)
wood=mat([.58,.31,.13],.62); woodtop=mat([.72,.46,.25],.58); black=mat([.025,.022,.02],.28); sleeve=mat([.08,.06,.05],.7); label=mat([.65,.34,.17],.8); metal=mat([.45,.43,.39],.22,.75)
# Render the actual exported build123d cabinet, not a hand-recreated proxy.
cabinet_file = ROOT / "exports" / "sparvik_assembly.stl"
cabinet = trimesh.load(cabinet_file, force="scene").dump(concatenate=True)
add(cabinet, wood)
# turntable, top bay
box((385,290,30),(275,-250,850),black); cyl=trimesh.creation.cylinder(125,8,sections=96); cyl.apply_translation((275,-205,870)); add(cyl,black)
hub=trimesh.creation.cylinder(8,10,sections=48);hub.apply_translation((275,-205,878));add(hub,label)
# tone arm
box((8,120,8),(405,-170,884),metal); box((8,8,45),(465,-110,905),metal)
# Open hinged dust cover at 45 degrees from the closed horizontal position.
# The hinge runs along X at the rear of the turntable; negative X rotation
# lifts the front edge upward while keeping the lid attached to the hinge.
lid_material = pyrender.MetallicRoughnessMaterial(
    baseColorFactor=[.42, .50, .54, .28],
    roughnessFactor=.12,
    metallicFactor=.0,
    alphaMode="BLEND",
)
# Build a shallow curved lid instead of a flat plate. The curvature is along
# the front-to-rear direction and is then rotated with the open hinge.
width, length, thickness, curvature = 450.0, 350.0, 6.0, -45.0
samples = 12
vertices = []
for layer in (-thickness / 2, thickness / 2):
    for i in range(samples + 1):
        s = -length / 2 + length * i / samples
        z_curve = curvature * (s / (length / 2)) ** 2
        vertices.extend([
            (275 - width / 2, -105 + s, 1025 + z_curve + layer),
            (275 + width / 2, -105 + s, 1025 + z_curve + layer),
        ])
faces = []
for i in range(samples):
    a, b = 2 * i, 2 * i + 2
    faces.extend([
        (a, a + 1, b + 1, b),
        (a + 1 + 2 * (samples + 1), a + 2 * (samples + 1), b + 2 * (samples + 1), b + 1 + 2 * (samples + 1)),
        (a, b, b + 2 * (samples + 1), a + 2 * (samples + 1)),
        (a + 1, a + 1 + 2 * (samples + 1), b + 1 + 2 * (samples + 1), b + 1),
    ])
faces.extend([
    (0, 2 * (samples + 1), 2 * (samples + 1) + 1, 1),
    (2 * samples, 2 * samples + 1, 4 * (samples + 1) - 1, 4 * (samples + 1) - 2),
])
lid = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
lid.apply_transform(
    trimesh.transformations.rotation_matrix(
        np.deg2rad(-45), [1, 0, 0], point=(275, -105, 1025)
    )
)
add(lid, lid_material)
# Dark perimeter contours make the curved acrylic lid read as a real formed
# dust cover instead of a floating flat rectangle.
rim_material = mat([.045, .055, .06], .28)
lid_rotation = trimesh.transformations.rotation_matrix(
    np.deg2rad(-45), [1, 0, 0], point=(275, -105, 1025)
)
def rim_segment(start, end):
    start, end = np.asarray(start, dtype=float), np.asarray(end, dtype=float)
    vector = end - start
    distance = np.linalg.norm(vector)
    tube = trimesh.creation.cylinder(radius=3.5, height=distance, sections=12)
    axis = np.cross([0, 0, 1], vector / distance)
    if np.linalg.norm(axis) > 1e-8:
        tube.apply_transform(trimesh.transformations.rotation_matrix(
            np.arccos(np.dot([0, 0, 1], vector / distance)), axis
        ))
    tube.apply_translation((start + end) / 2)
    tube.apply_transform(lid_rotation)
    add(tube, rim_material)

# Chamfered 45-degree corners give the lid a squared, formed-cover outline.
corner = 36.0
outline = [
    (-width / 2 + corner, -length / 2),
    ( width / 2 - corner, -length / 2),
    ( width / 2, -length / 2 + corner),
    ( width / 2,  length / 2 - corner),
    ( width / 2 - corner,  length / 2),
    (-width / 2 + corner,  length / 2),
    (-width / 2,  length / 2 - corner),
    (-width / 2, -length / 2 + corner),
]
def outline_point(x, s):
    return (275 + x, -105 + s, 1025 + curvature * (s / (length / 2)) ** 2)
outline = [outline_point(x, s) for x, s in outline]
for start, end in zip(outline, outline[1:] + outline[:1]):
    rim_segment(start, end)

# Small dark hinge cylinder makes the attachment read as real hardware.
hinge = trimesh.creation.cylinder(radius=5, height=330, sections=24)
hinge.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [0, 1, 0]))
hinge.apply_translation((275, -105, 1025))
add(hinge, mat([.04, .035, .03], .8))
# real CC0 speaker asset, scaled and placed to the right of the turntable
try:
 asset=trimesh.load(ROOT / 'assets' / 'cc0_speaker.glb', force='scene')
 asset=asset.dump(concatenate=True)
 scale=95/max(asset.extents)
 asset.apply_scale(scale)
 asset.apply_translation((385,-155,850)-asset.bounds.mean(axis=0))
 add(asset, mat([.12,.09,.065],.72))
except Exception as e: print('speaker skipped',e)
# Five simple, thin 3D vinyl sleeves per box. This restores the previous
# compact display: 225 mm high x 205 mm deep, with 12 mm thickness each.
# Box 1 is shifted left; box 2 is shifted right. No front panels are added.
RECORD_HEIGHT = 280
RECORD_DEPTH = 260
RECORD_THICKNESS = 12.0
record_materials = [
    mat([.06, .10, .14], .35),
    mat([.34, .14, .07], .42),
    mat([.08, .22, .13], .38),
    mat([.28, .07, .10], .45),
    mat([.34, .25, .08], .4),
]
for z, x_start in (
    (sparvik.DISC_BOX_1_FLOOR_Z, 60),
    (sparvik.DISC_BOX_2_FLOOR_Z, 420),
):
    for i, material in enumerate(record_materials):
        box(
            (RECORD_THICKNESS, RECORD_DEPTH, RECORD_HEIGHT),
            (x_start + i * RECORD_THICKNESS, -250, z + RECORD_HEIGHT / 2),
            material,
        )

# Optional purchased/downloaded Sketchfab Coleus model. Sketchfab marks the
# linked asset as royalty-free commercial content rather than a free download;
# place the legally obtained GLB at assets/potted_coleus.glb to enable it.
coleus_model = ROOT / "assets" / "potted_coleus.glb"
if coleus_model.exists():
    add_textured_asset(
        coleus_model,
        (220, 220, 390),
        (430, -220, 1455),
    )

# floor
floor=trimesh.creation.box(extents=(4000,4000,10));floor.apply_translation((275,-500,-10));add(floor,mat([.18,.15,.12],.9))
# Warm studio walls behind and to the right of the cabinet.
wall=trimesh.creation.box(extents=(3000,10,2200));wall.apply_translation((275,80,1100));add(wall,mat([.78,.74,.67],.95))
sidewall=trimesh.creation.box(extents=(10,3000,2200));sidewall.apply_translation((1400,-300,1100));add(sidewall,mat([.70,.67,.61],.95))
# camera and lights
def look_at(eye,target):
 f=(np.array(target)-np.array(eye));f=f/np.linalg.norm(f); up=np.array([0,0,1.]); r=np.cross(f,up);r=r/np.linalg.norm(r);u=np.cross(r,f);M=np.eye(4);M[:3,:3]=np.array([r,u,-f]).T;M[:3,3]=eye;return M
cam=pyrender.PerspectiveCamera(yfov=np.pi/4,aspectRatio=0.78)
scene.add(cam,pose=look_at((900,-2350,820),(275,-150,760)))
scene.add(pyrender.DirectionalLight(color=np.ones(3),intensity=3),pose=look_at((300,-500,1300),(275,-100,500)))
scene.add(pyrender.DirectionalLight(color=np.ones(3),intensity=1.3),pose=look_at((-500,200,800),(275,-100,600)))
scene.add(pyrender.PointLight(color=np.array([1,.75,.55]),intensity=80),pose=np.eye(4))
# Interior fill lights sit just in front of the back panel, lighting each
# compartment directly instead of relying on the distant studio lights.
scene.add(pyrender.PointLight(color=np.ones(3),intensity=350),pose=look_at((275,-360,1080),(275,-150,900)))
scene.add(pyrender.PointLight(color=np.ones(3),intensity=300),pose=look_at((275,-360,520),(275,-150,500)))
r=pyrender.OffscreenRenderer(900,1100); color,depth=r.render(scene, flags=pyrender.RenderFlags.SHADOWS_DIRECTIONAL); Image.fromarray(color).save(out); print(out)
