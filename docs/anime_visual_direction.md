# Anime Visual Direction

## Reference

The `anime` pack uses The Legend of Neverland as a high-level visual reference.
Its official store listing identifies the game as stylized Japanese anime and
shows strong character customization through face, hair, eyes, and fashion.

Reference:
https://play.google.com/store/apps/details?id=com.arkgames.ggplay.tlonglobal

This is an art-direction reference, not permission to reproduce its characters,
costumes, interfaces, logos, world lore, or exact assets.

## Translation Into Our Game

Our subject remains a persistent modern city viewed through a SimCity 4
Deluxe-like camera. The anime pack changes presentation, not simulation.

- bright, optimistic daylight and clean atmospheric perspective;
- readable silhouettes at an isometric street zoom;
- expressive adult anime faces without chibi proportions;
- sculpted hair made from a small number of clear strand masses;
- modern civilian clothing designed for the fashion economy;
- simplified materials with controlled highlights and soft color ramps;
- restrained outlines, used only when they improve close-up readability;
- cyan, sky blue, mint, coral, warm gold, and neutral ink surfaces;
- modern roads, apartments, shops, services, industry, and suburbs;
- no fantasy combat language, flower fairies, magical weapons, or copied UI.

## Character Contract

- Target proportion: about 6.75 to 7.25 heads tall.
- Two initial body presets share the canonical humanoid skeleton.
- Twenty faces vary identity through jaw, eyes, brows, nose, and mouth.
- Eyes are expressive but remain compatible with street-level viewing.
- Hair uses interchangeable rig-compatible meshes and shared materials.
- Clothing follows the existing semantic equipment slots.
- Portraits are rendered from the same 3D avatar used in the world.
- Dialogue adds blink, gaze, brows, jaw, smile, concern, and visemes.

## Rendering Contract

The first shader is a lightweight stylized-PBR hybrid:

- soft stepped diffuse response rather than hard two-tone cel shading;
- restrained skin and fabric specular;
- brighter hair highlights with broad shapes;
- face-shadow control that does not depend on arbitrary world rotation;
- subtle rim light for close dialogue shots;
- no full-screen outline pass for normal city gameplay.

The city uses the same lighting model with more realistic proportions and less
facial-style exaggeration. This keeps the world coherent without making modern
buildings look like fantasy props.

## Performance Budgets

- Cinematic LOD0: up to roughly 45k visible triangles for body, hair, and outfit.
- Street LOD1: target 15k to 20k visible triangles.
- Distance LOD2: simplified mesh or impostor below 5k triangles.
- District and city zoom: marker or aggregate crowd, no individual skinning.
- Maximum four material surfaces on a normal street avatar.
- 2K textures are reserved for close-up assets; street variants prefer 1K.
- Facial blend shapes and expensive hair effects activate only near the camera.

These are starting budgets and must be validated on the target mobile-class
device profile before content production expands.

## Animation Direction

The player never directly drives the avatar. Environment activities select
animation and movement.

- natural idle variation with slightly amplified readable poses;
- clean anticipation and follow-through, without combat exaggeration;
- contextual walk, sit, phone, talk, work, and vehicle transitions;
- facial expression layered over body animation;
- no constant emotes or decorative motion that turns the city into an MMO lobby.

## First Art Test

Build one original canonical avatar and one modern street corner:

1. one body and one face;
2. one hairstyle and one stock outfit;
3. idle, walk, sit, phone, and talk;
4. daylight plus evening lighting;
5. cinematic, street, and distance LOD;
6. portrait rendered from the same model.

The test succeeds when the avatar remains attractive in dialogue, readable at
street zoom, inexpensive at distance, and visually native to the modern city.
