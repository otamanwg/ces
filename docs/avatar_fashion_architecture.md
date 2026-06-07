# Avatar And Fashion Architecture

## Product Direction

The game follows the city-simulation perspective of SimCity 4 Deluxe, not the
direct character-control loop of The Sims.

- The player never steers the avatar.
- The environment and current activity select movement and animation.
- The city camera remains isometric and zoomable.
- At wide zoom the player is represented by a marker or aggregate crowd layer.
- At street zoom the real animated avatar, nickname, outfit, and interactions
  become visible.
- Story scenes use cinematic cameras. Subjective first-person shots may show
  hands or body, but the same canonical avatar remains the source of truth.

## Recommended Base Style

The first production style is stylized semi-realism with moderate geometry.

It is easier to keep visually consistent than hyperrealism, avoids an uncanny
face requirement, reads well from an isometric camera, and is light enough for
mobile-class devices. Future `anime`, `hyperreal`, and `mafia` packs map the
same semantic identity codes to different meshes and materials.

## Canonical Avatar Contract

One humanoid rig and one animation contract are shared by all initial avatars.

- Godot `SkeletonProfileHumanoid` is the retargeting target.
- All bodies, heads, hair, clothing, and accessories use the same bone names.
- Initial body customization is deliberately small: two body presets.
- Faces are preset identities, starting with 20 semantic face codes.
- A rendered portrait is generated from the 3D avatar when needed; it is not a
  separate identity asset.
- Clothing slots: `upper`, `lower`, `footwear`, `outerwear`, `headwear`,
  `accessory`.
- Initial animation states: `idle`, `walk`, `sit`, `phone`, `talk`,
  `work_generic`, `enter_vehicle`, `ride_vehicle`, `exit_vehicle`.
- Initial facial layer: blink, eye direction, jaw movement, smile, concern,
  and a small viseme set for dialogue.

## Environment-Driven Animation

The avatar consumes semantic activity commands rather than input:

```text
city simulation event
  -> avatar activity state
  -> navigation/seat/vehicle target
  -> animation state machine
  -> optional facial/dialogue layer
```

The server stores durable identity and equipped items. The client resolves
short-lived movement and animation from replicated city events.

## Rendering Levels

1. City zoom: no individual skinned characters.
2. District zoom: aggregate crowds or low-cost impostors.
3. Street zoom: full skinned avatars only near the camera.
4. Dialogue/cinematic: full avatar, facial layer, and higher-detail materials.

Automatic mesh LOD and visibility ranges are required. Full avatars must never
be the default representation for every resident in the city.

## Fashion Economy

Fashion is a social and economic metric, not a combat or progression gate.

### Supply Chain

1. AI suppliers sell approved fabrics, dyes, pattern licenses, and garment
   templates.
2. A player-owned design studio combines those inputs into a design.
3. An atelier or clothing factory produces inventory.
4. A stock or player-owned clothing shop sells physical items.
5. Purchased items enter player inventory and render on the avatar.

### Player Design Tool

The first version is parametric, not unrestricted file upload:

- garment template;
- material;
- palette;
- approved pattern;
- trim and logo placement;
- quality/production target;
- collection name and price.

This keeps UV layouts, rig compatibility, performance, copyright review, and
moderation manageable. Arbitrary texture or mesh uploads are a later,
moderated feature.

### Metrics

An outfit fashion score is derived from:

- garment quality;
- coordination between slots;
- current city trend;
- brand reputation;
- freshness and market saturation;
- context fit for the current activity.

Business profit additionally depends on material cost, production capacity,
stock, pricing, foot traffic, marketing, and competition. Trend fatigue and
anti-monopoly policy prevent one design from dominating forever.

### Business Doors

- stock clothing shop;
- player fashion boutique;
- design studio;
- tailor/atelier;
- textile workshop or factory;
- fashion house with collections and designer royalties.

Hair remains an AI city service initially. A hairstyle change is a paid
service, while player-run clothing businesses form the first creator economy.

## Delivery Order

1. Persist semantic avatar identity and expose it in player snapshots.
2. Build one canonical rig with one body, one head, one outfit, and core
   environment-driven animations.
3. Prove street-zoom rendering and LOD.
4. Add the second body, 20 face presets, hair, and stock outfits.
5. Add inventory/equipment.
6. Add fashion design, production, retail, trends, and royalties.
