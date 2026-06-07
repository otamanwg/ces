# Anime Visual Pack

This pack follows `docs/anime_visual_direction.md`.

It uses original assets with bright stylized lighting, adult anime characters,
clean silhouettes, sculpted hair, and modern civilian fashion. The Legend of
Neverland is a high-level rendering reference only; do not copy its characters,
costumes, UI, logos, fantasy motifs, or environments.

Required arrival assets:

- `arrival_waiting_hall_anime.png`
- `arrival_taxi_ride_anime.png`
- `arrival_bus_station_anime.png`
- `arrival_portrait_stranger_anime.png`
- `arrival_portrait_taxi_driver_anime.png`

Until a complete set exists, the style-pack resolver must continue falling back
to the neutral `core` assets.

Technical avatar preview:

```powershell
.\scripts\capture_anime_avatar.ps1 -Activity talk -Lod street
```
