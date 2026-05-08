
import math
import sys
import pygame
import numpy as np




WIDTH = 300
HEIGHT = 190
SCALE = 3


anti_aliasing_val = 4


reflection_depth = 1


def make_vec(x, y, z):
    return np.array([x, y, z], dtype=float)


def normalize(v):
    length = np.linalg.norm(v)
    if length == 0:
        return v
    return v / length


def clamp_color(color):
    return np.clip(color, 0, 1)


def reflect(direction, normal):
    return direction - 2 * np.dot(direction, normal) * normal




def make_material(color, diffuse, specular, shininess, reflectivity):
    return {
        "color": color,
        "diffuse": diffuse,
        "specular": specular,
        "shininess": shininess,
        "reflectivity": reflectivity
    }


red_material = make_material(make_vec(.95, .25, .20), .85, .15, 20, .10)
blue_material = make_material(make_vec(.20, .35, .95), .85, .20, 25, .15)
green_material = make_material(make_vec(.25, .80, .35), .85, .10, 15, .05)
gray_material = make_material(make_vec(.75, .75, .78), .70, .20, 30, .25)
floor_material = make_material(make_vec(.80, .80, .75), .75, .05, 8, .05)

objects = [
    {
        "kind": "sphere",
        "center": make_vec(-1.2, .0, -1.5),
        "radius": .75,
        "material": red_material
    },
    {
        "kind": "sphere",
        "center": make_vec(.35, -.1, -2.2),
        "radius": .90,
        "material": gray_material
    },
    {
        "kind": "sphere",
        "center": make_vec(1.55, -.25, -1.2),
        "radius": .60,
        "material": blue_material
    },
    {
        "kind": "sphere",
        "center": make_vec(.9, -.55, .20),
        "radius": .35,
        "material": green_material
    },
    {
        "kind": "plane",
        "point": make_vec(0, -1, 0),
        "normal": make_vec(0, 1, 0),
        "material": floor_material
    }
]

light_position = make_vec(2.5, 4.5, .5)
light_color = make_vec(1, 1, 1)

camera_position = make_vec(0, 1.1, 4.5)
camera_yaw = .0
camera_pitch = -.12




def hit_sphere(obj, ray_start, ray_dir):
    center = obj["center"]
    radius = obj["radius"]


    oc = ray_start - center
    a = np.dot(ray_dir, ray_dir)
    b = 2 * np.dot(oc, ray_dir)
    c = np.dot(oc, oc) - radius * radius

    discriminant = b * b - 4 * a * c

    if discriminant < 0:
        return None

    square_root = math.sqrt(discriminant)

    t1 = (-b - square_root) / (2 * a)
    t2 = (-b + square_root) / (2 * a)

    t = None

    if t1 > .001:
        t = t1
    elif t2 > .001:
        t = t2

    if t is None:
        return None

    hit_point = ray_start + t * ray_dir
    normal = normalize(hit_point - center)

    return {
        "t": t,
        "point": hit_point,
        "normal": normal,
        "material": obj["material"]
    }


def hit_plane(obj, ray_start, ray_dir):
    plane_point = obj["point"]
    plane_normal = normalize(obj["normal"])

    denominator = np.dot(plane_normal, ray_dir)

    if abs(denominator) < .0001:
        return None

    t = np.dot(plane_point - ray_start, plane_normal) / denominator

    if t <= .001:
        return None

    hit_point = ray_start + t * ray_dir
    material = obj["material"].copy()

    checker = (math.floor(hit_point[0]) + math.floor(hit_point[2])) % 2

    if checker == 0:
        material["color"] = make_vec(.80, .80, .75)
    else:
        material["color"] = make_vec(.25, .25, .27)

    return {
        "t": t,
        "point": hit_point,
        "normal": plane_normal,
        "material": material
    }


def find_closest_hit(ray_start, ray_dir):
    closest_hit = None
    closest_distance = 999999

    for obj in objects:
        if obj["kind"] == "sphere":
            hit = hit_sphere(obj, ray_start, ray_dir)
        else:
            hit = hit_plane(obj, ray_start, ray_dir)

        if hit is not None and hit["t"] < closest_distance:
            closest_distance = hit["t"]
            closest_hit = hit

    return closest_hit



def get_camera_vectors():
    global camera_yaw, camera_pitch

  
    forward = make_vec(
        math.sin(camera_yaw) * math.cos(camera_pitch),
        math.sin(camera_pitch),
        -math.cos(camera_yaw) * math.cos(camera_pitch)
    )
    forward = normalize(forward)

    world_up = make_vec(0, 1, 0)
    right = normalize(np.cross(forward, world_up))
    up = normalize(np.cross(right, forward))

    return forward, right, up


def get_ray_direction(pixel_x, pixel_y):
    forward, right, up = get_camera_vectors()

    aspect_ratio = WIDTH / HEIGHT
    fov = math.radians(60)
    fov_amount = math.tan(fov / 2)

    screen_x = (2 * pixel_x / WIDTH - 1) * aspect_ratio * fov_amount
    screen_y = (1 - 2 * pixel_y / HEIGHT) * fov_amount

    ray_dir = forward + screen_x * right + screen_y * up
    return normalize(ray_dir)




def is_in_shadow(point, normal):
    direction_to_light = light_position - point
    distance_to_light = np.linalg.norm(direction_to_light)
    direction_to_light = normalize(direction_to_light)


    shadow_start = point + normal * .001

    shadow_hit = find_closest_hit(shadow_start, direction_to_light)

    if shadow_hit is not None and shadow_hit["t"] < distance_to_light:
        return True

    return False


def background_color(ray_dir):

    t = .5 * (ray_dir[1] + 1)
    bottom_color = make_vec(.04, .05, .08)
    top_color = make_vec(.45, .65, .95)
    return bottom_color * (1 - t) + top_color * t


def trace_ray(ray_start, ray_dir, depth):
    hit = find_closest_hit(ray_start, ray_dir)

    if hit is None:
        return background_color(ray_dir)

    point = hit["point"]
    normal = hit["normal"]
    material = hit["material"]

    base_color = material["color"]


    final_color = base_color * .10

    if not is_in_shadow(point, normal):
        direction_to_light = normalize(light_position - point)


        diffuse_amount = max(np.dot(normal, direction_to_light), 0)
        diffuse_color = base_color * diffuse_amount * material["diffuse"]

        view_direction = normalize(-ray_dir)
        reflected_light = reflect(-direction_to_light, normal)
        specular_amount = max(np.dot(view_direction, reflected_light), 0)
        specular_amount = specular_amount ** material["shininess"]
        specular_color = light_color * specular_amount * material["specular"]

        final_color = final_color + diffuse_color + specular_color


    if depth > 0 and material["reflectivity"] > 0:
        reflected_dir = reflect(ray_dir, normal)
        reflected_start = point + normal * .001
        reflected_color = trace_ray(reflected_start, reflected_dir, depth - 1)

        reflectivity = material["reflectivity"]
        final_color = final_color * (1 - reflectivity) + reflected_color * reflectivity

    return clamp_color(final_color)


def render_scene(screen, font):
    global anti_aliasing_val

    image = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)


    sample_grid = int(math.sqrt(anti_aliasing_val))
    if sample_grid < 1:
        sample_grid = 1

    total_samples = sample_grid * sample_grid

    for y in range(HEIGHT):
        for x in range(WIDTH):
            color = make_vec(0, 0, 0)

 
            for sample_y in range(sample_grid):
                for sample_x in range(sample_grid):
                    offset_x = (sample_x + .5) / sample_grid
                    offset_y = (sample_y + .5) / sample_grid

                    ray_x = x + offset_x
                    ray_y = y + offset_y

                    ray_dir = get_ray_direction(ray_x, ray_y)
                    color = color + trace_ray(camera_position, ray_dir, reflection_depth)

            color = color / total_samples
            image[y, x] = clamp_color(color) * 255


        if y % 10 == 0:
            screen.fill((0, 0, 0))
            draw_text(screen, font, "Rendering... " + str(int(y / HEIGHT * 100)) + "%", 20, 20)
            pygame.display.flip()
            pygame.event.pump()

    return image




def draw_text(screen, font, text, x, y):
    text_image = font.render(text, True, (235, 235, 235))
    screen.blit(text_image, (x, y))


def draw_image(screen, image):

    surface = pygame.surfarray.make_surface(np.transpose(image, (1, 0, 2)))
    surface = pygame.transform.scale(surface, (WIDTH * SCALE, HEIGHT * SCALE))
    screen.blit(surface, (0, 0))


def draw_controls(screen, font):
    y = HEIGHT * SCALE + 8

    pygame.draw.rect(screen, (20, 20, 24), (0, HEIGHT * SCALE, WIDTH * SCALE, 90))

    draw_text(screen, font, "R render | WASD/QE move camera | Arrow keys rotate | IJKL/UO move light | +/- anti-aliasing | ESC quit", 10, y)
    draw_text(screen, font, "Anti-aliasing samples: " + str(anti_aliasing_val), 10, y + 25)
    draw_text(screen, font, "Camera: " + str(np.round(camera_position, 2)) + "   Light: " + str(np.round(light_position, 2)), 10, y + 50)



def handle_key(key):
    global camera_position
    global camera_yaw
    global camera_pitch
    global light_position
    global anti_aliasing_val

    forward, right, up = get_camera_vectors()

    move_amount = 1
    turn_amount = .08
    light_amount = 1

    if key == pygame.K_ESCAPE:
        pygame.quit()
        sys.exit()


    if key == pygame.K_w:
        camera_position = camera_position + forward * move_amount
    if key == pygame.K_s:
        camera_position = camera_position - forward * move_amount
    if key == pygame.K_a:
        camera_position = camera_position - right * move_amount
    if key == pygame.K_d:
        camera_position = camera_position + right * move_amount
    if key == pygame.K_q:
        camera_position = camera_position - up * move_amount
    if key == pygame.K_e:
        camera_position = camera_position + up * move_amount


    if key == pygame.K_LEFT:
        camera_yaw = camera_yaw - turn_amount
    if key == pygame.K_RIGHT:
        camera_yaw = camera_yaw + turn_amount
    if key == pygame.K_UP:
        camera_pitch = camera_pitch + turn_amount
    if key == pygame.K_DOWN:
        camera_pitch = camera_pitch - turn_amount

    if key == pygame.K_i:
        light_position = light_position + make_vec(0, 0, -light_amount)
    if key == pygame.K_k:
        light_position = light_position + make_vec(0, 0, light_amount)
    if key == pygame.K_j:
        light_position = light_position + make_vec(-light_amount, 0, 0)
    if key == pygame.K_l:
        light_position = light_position + make_vec(light_amount, 0, 0)
    if key == pygame.K_u:
        light_position = light_position + make_vec(0, light_amount, 0)
    if key == pygame.K_o:
        light_position = light_position + make_vec(0, -light_amount, 0)


    if key == pygame.K_PLUS or key == pygame.K_EQUALS or key == pygame.K_KP_PLUS:
        if anti_aliasing_val == 1:
            anti_aliasing_val = 4
        elif anti_aliasing_val == 4:
            anti_aliasing_val = 16

    if key == pygame.K_MINUS or key == pygame.K_KP_MINUS:
        if anti_aliasing_val == 16:
            anti_aliasing_val = 4
        elif anti_aliasing_val == 4:
            anti_aliasing_val = 1



def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH * SCALE, HEIGHT * SCALE + 90))
    pygame.display.set_caption("Beginner Ray Tracer")
    font = pygame.font.SysFont("consolas", 16)

    image = render_scene(screen, font)

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                handle_key(event.key)

                image = render_scene(screen, font)

        screen.fill((0, 0, 0))
        draw_image(screen, image)
        draw_controls(screen, font)
        pygame.display.flip()

    pygame.quit()


main()
