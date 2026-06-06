shader_type canvas_item;

uniform float horizontal_fade : hint_range(0.01, 0.3) = 0.1;
uniform float top_fade : hint_range(0.01, 0.3) = 0.06;
uniform float bottom_fade : hint_range(0.01, 0.4) = 0.18;

void fragment() {
	vec4 color = texture(TEXTURE, UV);
	float left_alpha = smoothstep(0.0, horizontal_fade, UV.x);
	float right_alpha = smoothstep(0.0, horizontal_fade, 1.0 - UV.x);
	float top_alpha = smoothstep(0.0, top_fade, UV.y);
	float bottom_alpha = smoothstep(0.0, bottom_fade, 1.0 - UV.y);
	color.a *= left_alpha * right_alpha * top_alpha * bottom_alpha;
	COLOR = color;
}
