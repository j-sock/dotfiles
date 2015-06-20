from PIL import Image, ImageDraw
from colorsys import hsv_to_rgb
import sys

MAX_VALUE = 255
SAT_MID = int(MAX_VALUE*0.67)
SAT_LOW = int(MAX_VALUE*0.33)
CONFIG_DIR = '/home/anna/.config/'
X_FILE = 'Xresources'
PANEL_FILE = 'bar/panel_colors'
NUM_COLOR_PAIRS = 9
MAX_DIST = 15

def main(image_path):
    image = Image.open(image_path)
    image_hsv = image.convert('HSV')
    width, height = image.size
    hues = [[None] * 3] * MAX_VALUE

    for x in range(width):
        for y in range(height):
            h, s, v = image_hsv.getpixel((x, y))
            sat_tier = get_sat_tier(s)
            if not hues[h][sat_tier]:
                hues[h][sat_tier] = {
                    'hue': h,
                    'pos': [(x, y)],
                    'sat_total': s,
                    'count': 1
                }
            else:
                hues[h][sat_tier]['pos'].append((x, y))
                hues[h][sat_tier]['sat_total'] += s
                hues[h][sat_tier]['count'] += 1

    hue_sat_choices = []
    for hue in hues:
        for sat in hue:
            if sat:
                sat['sat'] = int(sat['sat_total']/sat['count'])
                hue_sat_choices.append(sat)

    hue_sat_choices.sort(key=lambda x: -x['count'])
    
    colors = get_colors(hue_sat_choices, MAX_DIST)
    # draw_scheme(colors)
    write_x_scheme(colors)
    write_panel_scheme(colors)


def get_sat_tier(sat):
    if sat > SAT_MID: return 2
    elif sat > SAT_LOW: return 1
    else: return 0


def get_colors(hues, max_dist):
    colors = [((0, 0, int(MAX_VALUE*0.125)), (0, 0, int(MAX_VALUE*0.8)))]
    for hue in hues:
        h = hue['hue']
        if not has_similar(colors, h, max_dist):
            colors.append(((h, hue['sat'], int(MAX_VALUE*0.8)), (h, hue['sat'], MAX_VALUE)))
            if len(colors) == NUM_COLOR_PAIRS:
                return colors

    if len(colors) < NUM_COLOR_PAIRS:
        return fill_colors(colors, max_dist)

def fill_colors(colors, max_dist):
    if len(colors) > 1:
        dist = int(MAX_VALUE/2)
        while(len(colors) < NUM_COLOR_PAIRS and dist > 1):
            for i in range(1, len(colors)):
                inverse = colors[i][0][0] - dist
                if inverse < 0: inverse += MAX_VALUE
                if not has_similar(colors, inverse, max_dist):
                    colors.append(((inverse, colors[i][0][1], int(MAX_VALUE*0.8)), 
                                   (inverse, colors[i][0][1], MAX_VALUE)))
                    if len(colors) == NUM_COLOR_PAIRS:
                        return colors
            dist = int(dist/2)
        return colors

    dist = int(MAX_VALUE/(NUM_COLOR_PAIRS-1))
    for i in range(NUM_COLOR_PAIRS-1):
        colors.append(((i*dist, MAX_VALUE, int(MAX_VALUE*0.8), (i*dist, MAX_VALUE, MAX_VALUE))))
    return colors

def has_similar(colors, hue, max_dist):
    for color in colors:
            if is_similar_color(color[0][0], hue, max_dist):
                return True
    return False

def is_similar_color(h1, h2, max_dist):
    if h1 > MAX_VALUE and h2 < MAX_VALUE-max_dist:
        lower = h1 - MAX_VALUE + max_dist
        upper = h1 - MAX_VALUE - max_dist
    elif h1 < max_dist and h2 > MAX_VALUE-max_dist:
        lower = h1 + MAX_VALUE - max_dist
        upper = h1 + MAX_VALUE + max_dist
    else:
        lower = h1 - max_dist
        upper = h1 + max_dist
    
    if h2 > lower and h2 < upper:
        return True
    return False


def get_hex(color):
    h = color[0] / MAX_VALUE
    s = color[1] / MAX_VALUE
    v = color[2] / MAX_VALUE
    rgb = hsv_to_rgb(h, s, v)
    hex_rgb = hex(int(rgb[0] * 255))[2:], hex(int(rgb[1] * 255))[2:], hex(int(rgb[2] * 255))[2:]
    for value in hex_rgb:
        if len(value) == 1: value = '0' + value
    return '#' + hex_rgb[0] + hex_rgb[1] + hex_rgb[2]


def draw_scheme(colors):
    image = Image.new('HSV', (900, 400))
    image_draw = ImageDraw.Draw(image, mode='HSV')
    rect_len = int(800/len(colors))
    for i in range(0, len(colors)):
        c1, c2 = colors[i]
        image_draw.rectangle((i*rect_len, 0, (i+1)*rect_len, 200), fill=c1)
        image_draw.rectangle((i*rect_len, 200, (i+1)*rect_len, 400), fill=c2)
    del image_draw
    image.show()


def write_x_scheme(colors):
    color_read = open(CONFIG_DIR + X_FILE, 'r')
    old_text = color_read.read()
    color_read.close()
    old_text = old_text[:old_text.index('! terminal colors')]
    color_writeout = open(CONFIG_DIR + X_FILE, 'w')
    color_writeout.write(old_text + '! terminal colors' + ('-'*20) + '\n\n')
    background = get_hex(colors[0][0])
    foreground = get_hex(colors[0][1])
    color_writeout.write('*background: ' + background + '\n*foreground: ' + foreground + '\n')
    for index in range(1, len(colors)):
        dark = get_hex(colors[index][0])
        light = get_hex(colors[index][1])
        color_writeout.write('*color' + str(index-1) + ': ' + dark + 
                             '\n*color' + str(index + NUM_COLOR_PAIRS - 2) + ': ' + light + '\n')
    color_writeout.close()

def write_panel_scheme(colors):
    color_writeout = open(CONFIG_DIR + PANEL_FILE, 'w')
    background = get_hex(colors[0][0])
    text_bright = get_hex(colors[1][1])
    text_dark = get_hex(colors[1][0])
    color_writeout.write("COLOR_BACKGROUND='#ff" + background[1:] + "'\n\n")
    focous_fields = [
        'COLOR_ACTIVE_MONITOR_FG',
        'COLOR_FOCUSED_OCCUPIED_FG',
        'COLOR_FOCUSED_FREE_FG',
        'COLOR_FOCUSED_URGENT_FG',
        'COLOR_TITLE_FG',  # title
        'COLOR_STATUS_FG'  # output
    ]
    unfocous_fields = [
        'COLOR_INACTIVE_MONITOR_FG',
        'COLOR_OCCUPIED_FG',
        'COLOR_FREE_FG',
        'COLOR_URGENT_FG'
    ]
    for field in focous_fields:
        color_writeout.write(field + "='#ff" + text_bright[1:] + "'\n")
    color_writeout.write('\n')
    for field in unfocous_fields:
        color_writeout.write(field + "='#ff" + text_dark[1:] + "'\n")
    color_writeout.close()


if __name__ == '__main__':
    main(sys.argv[1])
