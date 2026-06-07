# Blender Asset Pipeline

The project uses portable Blender 4.5 LTS from:

https://download.blender.org/release/Blender4.5/

Local executable:

```text
C:\Tools\Blender\blender-4.5.4-windows-x64\blender.exe
```

Generate the original canonical anime avatar:

```powershell
.\scripts\build_anime_avatar.ps1
```

The Python generator is the editable source of truth. It creates:

- a humanoid armature with semantic Godot-compatible bone names;
- an original stylized mesh and materials;
- modular low-poly mesh groups for seven hairstyles; `hair_bald` hides them all;
- `idle`, `walk`, `sit`, `phone`, and `talk` actions;
- a GLB in `client/assets/visual/anime/avatar`.

The generated `.blend` file is kept under `.tools` for inspection and is not
required to reproduce the committed GLB.

Facial morph targets are intentionally deferred until the head uses dedicated
expression topology. The first thin-mouth morph prototype produced invalid LOD
normals in Godot and was removed instead of suppressing the importer warning.
