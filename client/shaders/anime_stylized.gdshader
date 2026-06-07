shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

uniform vec4 base_color : source_color = vec4(0.8, 0.8, 0.8, 1.0);
uniform vec4 shadow_tint : source_color = vec4(0.32, 0.38, 0.48, 1.0);
uniform vec4 rim_color : source_color = vec4(0.62, 0.86, 0.94, 1.0);
uniform float roughness : hint_range(0.0, 1.0) = 0.72;
uniform float shade_threshold : hint_range(0.0, 1.0) = 0.48;
uniform float shade_softness : hint_range(0.01, 0.5) = 0.16;
uniform float rim_strength : hint_range(0.0, 1.0) = 0.07;

void fragment() {
	ALBEDO = base_color.rgb;
	ROUGHNESS = roughness;
	SPECULAR = 0.24;
}

void light() {
	float light_facing = dot(NORMAL, LIGHT) * 0.5 + 0.5;
	float shade = smoothstep(
		shade_threshold - shade_softness,
		shade_threshold + shade_softness,
		light_facing
	);
	vec3 banded_color = mix(shadow_tint.rgb, base_color.rgb, shade);
	DIFFUSE_LIGHT += banded_color * LIGHT_COLOR * ATTENUATION;

	float rim = pow(1.0 - max(dot(NORMAL, VIEW), 0.0), 3.0);
	SPECULAR_LIGHT += rim_color.rgb * rim * rim_strength * ATTENUATION;
}
