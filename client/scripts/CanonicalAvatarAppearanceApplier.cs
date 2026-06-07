using System;
using Godot;

#nullable enable

public static class CanonicalAvatarAppearanceApplier
{
    public static void Apply(Node root, AvatarAppearance appearance, Shader? stylizedShader = null)
    {
        var skinMaterial = CreateMaterial(ToColor(appearance.SkinColor), stylizedShader);
        var hairMaterial = CreateMaterial(ToColor(appearance.HairColor), stylizedShader);
        var upperMaterial = CreateMaterial(ToColor(appearance.UpperColor), stylizedShader);
        var lowerMaterial = CreateMaterial(ToColor(appearance.LowerColor), stylizedShader);
        var footwearMaterial = CreateMaterial(ToColor(appearance.FootwearColor), stylizedShader);

        VisitMeshes(root, mesh =>
        {
            string name = mesh.Name.ToString();
            if (name.StartsWith("Hair", StringComparison.Ordinal))
            {
                mesh.Visible = IsVisibleHairGroup(name, appearance);
                mesh.MaterialOverride = hairMaterial;
                return;
            }
            if (name is "FaceMesh" or "LowerArmLeft" or "LowerArmRight"
                or "HandLeft" or "HandRight" or "LowerLegLeft" or "LowerLegRight")
            {
                mesh.MaterialOverride = skinMaterial;
            }
            else if (name is "TorsoMesh" or "UpperArmLeft" or "UpperArmRight")
            {
                mesh.MaterialOverride = upperMaterial;
            }
            else if (name is "HipsMesh" or "UpperLegLeft" or "UpperLegRight")
            {
                mesh.MaterialOverride = lowerMaterial;
            }
            else if (name is "FootLeft" or "FootRight")
            {
                mesh.MaterialOverride = footwearMaterial;
            }
        });

        ScaleMesh(root, "TorsoMesh", new Vector3(appearance.TorsoWidthScale, 1.0f, appearance.TorsoWidthScale));
        ScaleMesh(root, "HipsMesh", new Vector3(appearance.TorsoWidthScale, 1.0f, appearance.TorsoWidthScale));
        ScaleMesh(root, "UpperArmLeft", new Vector3(appearance.LimbWidthScale, appearance.LimbWidthScale, 1.0f));
        ScaleMesh(root, "UpperArmRight", new Vector3(appearance.LimbWidthScale, appearance.LimbWidthScale, 1.0f));
        ScaleMesh(
            root,
            "FaceMesh",
            new Vector3(appearance.Face.HeadWidthScale, appearance.Face.HeadHeightScale, 1.0f)
        );
        ScaleMesh(root, "EyeLeft", Vector3.One * appearance.Face.EyeScale);
        ScaleMesh(root, "EyeRight", Vector3.One * appearance.Face.EyeScale);
        ScaleMesh(root, "Mouth", new Vector3(appearance.Face.MouthWidthScale, 1.0f, 1.0f));
        OffsetEye(root, "EyeLeft", appearance);
        OffsetEye(root, "EyeRight", appearance);
    }

    public static T? FindDescendant<T>(Node root) where T : Node
    {
        if (root is T match)
        {
            return match;
        }
        foreach (Node child in root.GetChildren())
        {
            var descendant = FindDescendant<T>(child);
            if (descendant != null)
            {
                return descendant;
            }
        }
        return null;
    }

    private static void OffsetEye(Node root, string name, AvatarAppearance appearance)
    {
        var eye = FindDescendantByName<MeshInstance3D>(root, name);
        if (eye == null)
        {
            return;
        }
        eye.Position = new Vector3(
            eye.Position.X * appearance.Face.EyeSpacingScale,
            eye.Position.Y + appearance.Face.EyeHeightOffset,
            eye.Position.Z
        );
    }

    private static void ScaleMesh(Node root, string name, Vector3 scale)
    {
        var mesh = FindDescendantByName<MeshInstance3D>(root, name);
        if (mesh != null)
        {
            mesh.Scale *= scale;
        }
    }

    private static bool IsVisibleHairGroup(string meshName, AvatarAppearance appearance)
    {
        foreach (string group in appearance.VisibleHairGroups)
        {
            if (meshName.StartsWith(group, StringComparison.Ordinal))
            {
                return true;
            }
        }
        return false;
    }

    private static T? FindDescendantByName<T>(Node root, string name) where T : Node
    {
        if (root is T match && root.Name.ToString() == name)
        {
            return match;
        }
        foreach (Node child in root.GetChildren())
        {
            var descendant = FindDescendantByName<T>(child, name);
            if (descendant != null)
            {
                return descendant;
            }
        }
        return null;
    }

    private static void VisitMeshes(Node root, Action<MeshInstance3D> visit)
    {
        if (root is MeshInstance3D mesh)
        {
            visit(mesh);
        }
        foreach (Node child in root.GetChildren())
        {
            VisitMeshes(child, visit);
        }
    }

    private static Material CreateMaterial(Color color, Shader? shader)
    {
        if (shader == null)
        {
            return new StandardMaterial3D { AlbedoColor = color, Roughness = 0.76f };
        }
        var material = new ShaderMaterial { Shader = shader };
        material.SetShaderParameter("base_color", color);
        material.SetShaderParameter("shadow_tint", color.Darkened(0.48f));
        return material;
    }

    private static Color ToColor(AvatarColorToken token)
    {
        return new Color(token.Red, token.Green, token.Blue);
    }
}
