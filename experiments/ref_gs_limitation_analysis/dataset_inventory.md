# Ref-GS Dataset Inventory

Root: `/data/liuly/dataset/3DGS`
Scene candidates: 106
Stock-loader compatible: 93

## Layout Counts

- blender_transforms: 30
- colmap_direct: 68
- image_or_auxiliary: 2
- unknown: 6

## Dataset Counts

- DTU: 15
- GlossySynthetic: 8
- GlossySyntheticConverted: 8
- NeRF Synthetic: 8
- Shiny Blender Real: 3
- Shiny Blender Synthetic: 6
- glossy: 10
- llff_colmap_LDR: 42
- priors: 6

## Small Sanity Candidates

- `Shiny Blender Synthetic/ball` (blender_transforms), images=900, train=100, test=200, size_mb=129.86, eval_pts=False, meshes=2
- `GlossySynthetic/bell_blender` (blender_transforms), images=0, train=112, test=16, size_mb=91.38, eval_pts=False, meshes=1
- `GlossySyntheticConverted/bell_blender` (blender_transforms), images=0, train=112, test=16, size_mb=95.22, eval_pts=True, meshes=3
- `NeRF Synthetic/mic` (blender_transforms), images=500, train=100, test=200, size_mb=95.56, eval_pts=False, meshes=0
- `GlossySynthetic/potion_blender` (blender_transforms), images=0, train=112, test=16, size_mb=96.15, eval_pts=False, meshes=1
- `GlossySynthetic/angel_blender` (blender_transforms), images=0, train=112, test=16, size_mb=98.01, eval_pts=False, meshes=1
- `GlossySynthetic/cat_blender` (blender_transforms), images=0, train=112, test=16, size_mb=98.06, eval_pts=False, meshes=1
- `GlossySyntheticConverted/potion_blender` (blender_transforms), images=0, train=112, test=16, size_mb=101.34, eval_pts=True, meshes=3
- `GlossySyntheticConverted/angel_blender` (blender_transforms), images=0, train=112, test=16, size_mb=101.42, eval_pts=True, meshes=3
- `GlossySynthetic/teapot_blender` (blender_transforms), images=0, train=112, test=16, size_mb=101.92, eval_pts=False, meshes=1
- `GlossySyntheticConverted/cat_blender` (blender_transforms), images=0, train=112, test=16, size_mb=102.2, eval_pts=True, meshes=3
- `GlossySynthetic/tbell_blender` (blender_transforms), images=0, train=112, test=16, size_mb=104.25, eval_pts=False, meshes=1

## Scenes

- `DTU/scan105`: layout=colmap_direct, compatible=True, images=64, train=0, test=0, sparse=True, masks=128, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan106`: layout=colmap_direct, compatible=True, images=64, train=0, test=0, sparse=True, masks=65, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan110`: layout=colmap_direct, compatible=True, images=64, train=0, test=0, sparse=True, masks=67, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan114`: layout=colmap_direct, compatible=True, images=64, train=0, test=0, sparse=True, masks=64, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan118`: layout=colmap_direct, compatible=True, images=64, train=0, test=0, sparse=True, masks=64, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan122`: layout=colmap_direct, compatible=True, images=64, train=0, test=0, sparse=True, masks=128, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan24`: layout=colmap_direct, compatible=True, images=49, train=0, test=0, sparse=True, masks=98, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan37`: layout=colmap_direct, compatible=True, images=49, train=0, test=0, sparse=True, masks=97, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan40`: layout=colmap_direct, compatible=True, images=49, train=0, test=0, sparse=True, masks=98, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan55`: layout=colmap_direct, compatible=True, images=49, train=0, test=0, sparse=True, masks=98, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan63`: layout=colmap_direct, compatible=True, images=49, train=0, test=0, sparse=True, masks=97, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan65`: layout=colmap_direct, compatible=True, images=49, train=0, test=0, sparse=True, masks=49, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan69`: layout=colmap_direct, compatible=True, images=49, train=0, test=0, sparse=True, masks=95, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan83`: layout=colmap_direct, compatible=True, images=64, train=0, test=0, sparse=True, masks=128, depth=0, normal=0, meshes=1, eval_pts=False
- `DTU/scan97`: layout=colmap_direct, compatible=True, images=64, train=0, test=0, sparse=True, masks=64, depth=0, normal=0, meshes=1, eval_pts=False
- `glossy/GlossyReal/bear`: layout=colmap_direct, compatible=True, images=97, train=0, test=0, sparse=True, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `glossy/GlossyReal/bear/colmap`: layout=colmap_direct, compatible=False, images=0, train=0, test=0, sparse=True, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `glossy/GlossyReal/bunny`: layout=colmap_direct, compatible=True, images=129, train=0, test=0, sparse=True, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `glossy/GlossyReal/bunny/colmap`: layout=colmap_direct, compatible=False, images=0, train=0, test=0, sparse=True, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `glossy/GlossyReal/coral`: layout=colmap_direct, compatible=True, images=126, train=0, test=0, sparse=True, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `glossy/GlossyReal/coral/colmap`: layout=colmap_direct, compatible=False, images=0, train=0, test=0, sparse=True, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `glossy/GlossyReal/maneki`: layout=image_or_auxiliary, compatible=False, images=128, train=0, test=0, sparse=False, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `glossy/GlossyReal/maneki/colmap`: layout=colmap_direct, compatible=False, images=0, train=0, test=0, sparse=True, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `glossy/GlossyReal/vase`: layout=image_or_auxiliary, compatible=False, images=128, train=0, test=0, sparse=False, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `glossy/GlossyReal/vase/colmap`: layout=colmap_direct, compatible=False, images=0, train=0, test=0, sparse=True, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `GlossySynthetic/angel_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `GlossySynthetic/bell_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `GlossySynthetic/cat_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `GlossySynthetic/horse_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `GlossySynthetic/luyu_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `GlossySynthetic/potion_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `GlossySynthetic/tbell_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `GlossySynthetic/teapot_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=1, eval_pts=False
- `GlossySyntheticConverted/angel_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=3, eval_pts=True
- `GlossySyntheticConverted/bell_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=3, eval_pts=True
- `GlossySyntheticConverted/cat_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=3, eval_pts=True
- `GlossySyntheticConverted/horse_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=3, eval_pts=True
- `GlossySyntheticConverted/luyu_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=3, eval_pts=True
- `GlossySyntheticConverted/potion_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=3, eval_pts=True
- `GlossySyntheticConverted/tbell_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=3, eval_pts=True
- `GlossySyntheticConverted/teapot_blender`: layout=blender_transforms, compatible=True, images=0, train=112, test=16, sparse=False, masks=0, depth=0, normal=0, meshes=3, eval_pts=True
- `llff_colmap_LDR/baking_scene001`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/baking_scene002`: layout=colmap_direct, compatible=True, images=69, train=0, test=0, sparse=True, masks=69, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/baking_scene003`: layout=colmap_direct, compatible=True, images=69, train=0, test=0, sparse=True, masks=69, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/ball_scene002`: layout=colmap_direct, compatible=True, images=69, train=0, test=0, sparse=True, masks=69, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/ball_scene003`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/ball_scene004`: layout=colmap_direct, compatible=True, images=73, train=0, test=0, sparse=True, masks=73, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/blocks_scene002`: layout=colmap_direct, compatible=True, images=69, train=0, test=0, sparse=True, masks=69, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/blocks_scene005`: layout=colmap_direct, compatible=True, images=71, train=0, test=0, sparse=True, masks=71, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/blocks_scene006`: layout=colmap_direct, compatible=True, images=75, train=0, test=0, sparse=True, masks=75, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/cactus_scene001`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/cactus_scene005`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/cactus_scene007`: layout=colmap_direct, compatible=True, images=71, train=0, test=0, sparse=True, masks=71, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/car_scene002`: layout=colmap_direct, compatible=True, images=71, train=0, test=0, sparse=True, masks=71, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/car_scene004`: layout=colmap_direct, compatible=True, images=74, train=0, test=0, sparse=True, masks=74, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/car_scene006`: layout=colmap_direct, compatible=True, images=71, train=0, test=0, sparse=True, masks=71, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/chips_scene002`: layout=colmap_direct, compatible=True, images=72, train=0, test=0, sparse=True, masks=72, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/chips_scene003`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/chips_scene004`: layout=colmap_direct, compatible=True, images=71, train=0, test=0, sparse=True, masks=71, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/cup_scene003`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/cup_scene006`: layout=colmap_direct, compatible=True, images=69, train=0, test=0, sparse=True, masks=69, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/cup_scene007`: layout=colmap_direct, compatible=True, images=72, train=0, test=0, sparse=True, masks=72, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/curry_scene001`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/curry_scene005`: layout=colmap_direct, compatible=True, images=72, train=0, test=0, sparse=True, masks=72, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/curry_scene007`: layout=colmap_direct, compatible=True, images=72, train=0, test=0, sparse=True, masks=72, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/gnome_scene003`: layout=colmap_direct, compatible=True, images=71, train=0, test=0, sparse=True, masks=71, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/gnome_scene005`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/gnome_scene007`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/grogu_scene001`: layout=colmap_direct, compatible=True, images=69, train=0, test=0, sparse=True, masks=69, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/grogu_scene002`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/grogu_scene003`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/pepsi_scene002`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/pepsi_scene003`: layout=colmap_direct, compatible=True, images=71, train=0, test=0, sparse=True, masks=71, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/pepsi_scene004`: layout=colmap_direct, compatible=True, images=72, train=0, test=0, sparse=True, masks=72, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/pitcher_scene001`: layout=colmap_direct, compatible=True, images=68, train=0, test=0, sparse=True, masks=68, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/pitcher_scene005`: layout=colmap_direct, compatible=True, images=71, train=0, test=0, sparse=True, masks=71, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/pitcher_scene007`: layout=colmap_direct, compatible=True, images=71, train=0, test=0, sparse=True, masks=71, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/salt_scene004`: layout=colmap_direct, compatible=True, images=76, train=0, test=0, sparse=True, masks=76, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/salt_scene005`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/salt_scene007`: layout=colmap_direct, compatible=True, images=75, train=0, test=0, sparse=True, masks=75, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/teapot_scene001`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/teapot_scene002`: layout=colmap_direct, compatible=True, images=70, train=0, test=0, sparse=True, masks=70, depth=0, normal=0, meshes=0, eval_pts=False
- `llff_colmap_LDR/teapot_scene006`: layout=colmap_direct, compatible=True, images=71, train=0, test=0, sparse=True, masks=71, depth=0, normal=0, meshes=0, eval_pts=False
- `NeRF Synthetic/chair`: layout=blender_transforms, compatible=True, images=500, train=100, test=200, sparse=False, masks=0, depth=200, normal=0, meshes=0, eval_pts=False
- `NeRF Synthetic/drums`: layout=blender_transforms, compatible=True, images=500, train=100, test=200, sparse=False, masks=0, depth=200, normal=0, meshes=0, eval_pts=False
- `NeRF Synthetic/ficus`: layout=blender_transforms, compatible=True, images=500, train=100, test=200, sparse=False, masks=0, depth=200, normal=0, meshes=0, eval_pts=False
- `NeRF Synthetic/hotdog`: layout=blender_transforms, compatible=True, images=500, train=100, test=200, sparse=False, masks=0, depth=200, normal=0, meshes=0, eval_pts=False
- `NeRF Synthetic/lego`: layout=blender_transforms, compatible=True, images=500, train=100, test=200, sparse=False, masks=0, depth=200, normal=0, meshes=0, eval_pts=False
- `NeRF Synthetic/materials`: layout=blender_transforms, compatible=True, images=500, train=100, test=200, sparse=False, masks=0, depth=200, normal=0, meshes=0, eval_pts=False
- `NeRF Synthetic/mic`: layout=blender_transforms, compatible=True, images=500, train=100, test=200, sparse=False, masks=0, depth=200, normal=0, meshes=0, eval_pts=False
- `NeRF Synthetic/ship`: layout=blender_transforms, compatible=True, images=531, train=100, test=200, sparse=False, masks=0, depth=200, normal=31, meshes=0, eval_pts=False
- `priors/Ref-NeRF/refnerf/ball`: layout=unknown, compatible=False, images=0, train=0, test=0, sparse=False, masks=0, depth=0, normal=0, meshes=0, eval_pts=False
- `priors/Ref-NeRF/refnerf/car`: layout=unknown, compatible=False, images=0, train=0, test=0, sparse=False, masks=0, depth=0, normal=0, meshes=0, eval_pts=False
- `priors/Ref-NeRF/refnerf/coffee`: layout=unknown, compatible=False, images=0, train=0, test=0, sparse=False, masks=0, depth=0, normal=0, meshes=0, eval_pts=False
- `priors/Ref-NeRF/refnerf/helmet`: layout=unknown, compatible=False, images=0, train=0, test=0, sparse=False, masks=0, depth=0, normal=0, meshes=0, eval_pts=False
- `priors/Ref-NeRF/refnerf/teapot`: layout=unknown, compatible=False, images=0, train=0, test=0, sparse=False, masks=0, depth=0, normal=0, meshes=0, eval_pts=False
- `priors/Ref-NeRF/refnerf/toaster`: layout=unknown, compatible=False, images=0, train=0, test=0, sparse=False, masks=0, depth=0, normal=0, meshes=0, eval_pts=False
- `Shiny Blender Real/gardenspheres`: layout=colmap_direct, compatible=True, images=151, train=0, test=0, sparse=True, masks=0, depth=0, normal=0, meshes=0, eval_pts=False
- `Shiny Blender Real/sedan`: layout=colmap_direct, compatible=True, images=158, train=0, test=0, sparse=True, masks=0, depth=0, normal=0, meshes=0, eval_pts=False
- `Shiny Blender Real/toycar`: layout=colmap_direct, compatible=True, images=122, train=0, test=0, sparse=True, masks=0, depth=0, normal=0, meshes=0, eval_pts=False
- `Shiny Blender Synthetic/ball`: layout=blender_transforms, compatible=True, images=900, train=100, test=200, sparse=False, masks=300, depth=0, normal=300, meshes=2, eval_pts=False
- `Shiny Blender Synthetic/car`: layout=blender_transforms, compatible=True, images=600, train=100, test=200, sparse=False, masks=0, depth=300, normal=300, meshes=2, eval_pts=False
- `Shiny Blender Synthetic/coffee`: layout=blender_transforms, compatible=True, images=600, train=100, test=200, sparse=False, masks=0, depth=300, normal=300, meshes=2, eval_pts=False
- `Shiny Blender Synthetic/helmet`: layout=blender_transforms, compatible=True, images=600, train=100, test=200, sparse=False, masks=0, depth=300, normal=300, meshes=2, eval_pts=False
- `Shiny Blender Synthetic/teapot`: layout=blender_transforms, compatible=True, images=600, train=100, test=200, sparse=False, masks=0, depth=300, normal=300, meshes=2, eval_pts=False
- `Shiny Blender Synthetic/toaster`: layout=blender_transforms, compatible=True, images=600, train=100, test=200, sparse=False, masks=0, depth=300, normal=300, meshes=2, eval_pts=False
