# =====================================================================
#  격자지도에서 이동경로 최소화
# ---------------------------------------------------------------------
#  실행 방법:  python main.py        (pygame 이 필요: pip install pygame)
#
#  [조작법]
#   - 처음 화면에서 지도 크기 입력 (예: 5*5, 10*8  -> 가로 * 세로)
#       * 가로나 세로가 10 이상이면 지도 일부만 보이고,
#         마우스 휠(가운데 버튼)을 누른 채 끌어서 화면을 이동
#       * 10보다 작으면 지도 전체가 화면에 맞게 보임
#   - [랜덤] 버튼          : 길, 장애물, 출발점, 도착점을 무작위로 만들기
#   - 땅 왼쪽 클릭        : 땅 활성화 / 비활성화
#   - 활성화된 땅 오른쪽 클릭 : 메뉴 (장애물 / 연결 / 출발점 / 도착점)
#       * "연결"을 고른 뒤 다른 활성화된 땅을 왼쪽 클릭하면 선으로 연결
#   - 연결선 왼쪽 클릭     : 연결 해제
#   - 연결선 오른쪽 클릭    : 거리 입력 (입력하지 않으면 거리 1)
#   - 출발점과 도착점이 있으면 [시작] 버튼이 켜짐
#   - 시뮬레이션 중 스페이스바 : 남은 탐색 건너뛰기
# =====================================================================

import math
import os
import random
import pygame

# ---------------------------------------------------------------------
# 1. 기본 설정 값 (숫자를 바꾸면 화면 모양이 바뀝니다)
# ---------------------------------------------------------------------
WIDTH, HEIGHT = 1000, 700       # 창 크기
GRID_COLS = 5                   # 가로 칸 수 (처음 화면에서 바뀜)
GRID_ROWS = 5                   # 세로 줄 수 (처음 화면에서 바뀜)
MAX_SIZE = 26                   # 가로/세로 최대 크기 (칸 이름이 A~Z 라서)
SCROLL_SIZE = 10                # 가로나 세로가 이 값 이상이면 '일부만 보이기 + 끌어서 이동'
CELL = 100                      # 땅 한 칸의 크기(픽셀). 작은 지도에서는 화면에 맞게 줄어듦
GAP = 24                        # 땅과 땅 사이 간격 (CELL 에 맞춰 바뀜)
GRID_X, GRID_Y = 50, 70         # 격자가 그려지기 시작하는 위치(왼쪽 위)
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MAX_ROUTES = 500                # 길이 너무 많으면 여기까지만 탐색 (프로그램이 멈추지 않게)

# 지도가 보이는 영역 (화면 왼쪽)
VIEW = pygame.Rect(0, 0, 670, HEIGHT)
FPS = 60                        # 1초에 화면을 몇 번 다시 그릴지
ROBOT_SPEED = 4                 # 로봇이 한 프레임에 움직이는 거리(픽셀)

# 색깔 (빨강, 초록, 파랑)
BG_COLOR = (25, 28, 36)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
LINE_COLOR = (90, 200, 255)
PATH_COLOR = (255, 210, 60)
OK_COLOR = (90, 220, 120)
FAIL_COLOR = (240, 90, 90)

# 이미지 파일이 있는 폴더 (이 파이썬 파일과 같은 폴더)
FOLDER = os.path.dirname(os.path.abspath(__file__))

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("격자지도에서 이동경로 최소화")
clock = pygame.time.Clock()


# ---------------------------------------------------------------------
# 2. 글꼴과 이미지 불러오기
# ---------------------------------------------------------------------
def load_font(size):
    """한글이 나오는 글꼴을 불러옵니다. (윈도우: 맑은 고딕)"""
    return pygame.font.SysFont("malgungothic,applegothic,nanumgothic", size)


FONT_BIG = load_font(32)
FONT = load_font(20)
FONT_SMALL = load_font(16)


def load_image(filename, max_w, max_h):
    """이미지를 불러와서 빈 여백을 잘라내고, (max_w, max_h) 안에 들어가게 줄입니다."""
    image = pygame.image.load(os.path.join(FOLDER, filename)).convert_alpha()
    # 거의 투명한 여백(빛 번짐 등)을 잘라내기
    image = image.subsurface(image.get_bounding_rect(min_alpha=60)).copy()
    # 가로세로 비율을 지키면서 크기 맞추기
    w, h = image.get_size()
    scale = min(max_w / w, max_h / h)
    return pygame.transform.smoothscale(image, (int(w * scale), int(h * scale)))


# 지도 위 오브젝트 이미지들 (땅 크기 CELL 에 맞춰야 해서 함수로 만듦)
def load_map_images():
    """땅 크기(CELL)에 맞게 지도 그림들을 불러오기. 지도 크기가 바뀔 때마다 다시 부름"""
    global place_img, place_off_img, hole_img, start_img, end_img, robot_img
    place_img = load_image("place_object.png", CELL, CELL)              # 활성화된 땅
    hole_img = load_image("holl_object.png", CELL * 0.8, CELL * 0.8)      # 장애물
    start_img = load_image("start_object.png", CELL * 0.8, CELL * 0.8)    # 출발점
    end_img = load_image("end_object.png", CELL * 0.8, CELL * 0.8)        # 도착점
    robot_img = load_image("robot_object.png", CELL * 0.75, CELL * 0.75)  # 로봇 (왼쪽이 앞)

    # 비활성화된 땅: 활성화 땅 그림을 어둡게 만든 것
    place_off_img = place_img.copy()
    place_off_img.fill((70, 70, 70), special_flags=pygame.BLEND_RGB_MULT)


load_map_images()

# 버튼 이미지들
go_img = load_image("go_butten_object.png", 240, 80)            # 시작 버튼
back_img = load_image("back_butten_object.png", 180, 60)        # 나가기 버튼

# 꺼진 시작 버튼: 시작 버튼을 회색으로 만든 것
go_off_img = pygame.transform.grayscale(go_img)

# 길 보기 버튼 (make_objects.py 로 만든 그림, 없으면 바로 그려서 사용)
if os.path.exists(os.path.join(FOLDER, "view_butten_object.png")):
    view_img = load_image("view_butten_object.png", 100, 36)
else:
    view_img = pygame.Surface((100, 36), pygame.SRCALPHA)
    pygame.draw.rect(view_img, (40, 120, 230), view_img.get_rect(), border_radius=12)
    label = FONT_SMALL.render("길 보기", True, WHITE)
    view_img.blit(label, label.get_rect(center=(50, 18)))

# 랜덤 버튼 (make_objects.py 로 만든 그림, 없으면 바로 그려서 사용)
if os.path.exists(os.path.join(FOLDER, "random_butten_object.png")):
    random_img = load_image("random_butten_object.png", 200, 60)
else:
    random_img = pygame.Surface((180, 60), pygame.SRCALPHA)
    pygame.draw.rect(random_img, (150, 70, 220), random_img.get_rect(), border_radius=20)
    label = FONT.render("랜덤", True, WHITE)
    random_img.blit(label, label.get_rect(center=(90, 30)))

# 버튼 위치
go_rect = go_img.get_rect(center=(820, 120))
random_rect = random_img.get_rect(center=(820, 205))
back_rect = back_img.get_rect(bottomright=(WIDTH - 20, HEIGHT - 20))


# ---------------------------------------------------------------------
# 3. 게임 데이터 (지도 상태)
# ---------------------------------------------------------------------
# active[줄][칸] = True 이면 활성화된 땅 (지도 크기를 정한 뒤 make_map() 에서 만듦)
active = []

# roles[(줄, 칸)] = "hole"(장애물) / "start"(출발점) / "end"(도착점)
roles = {}

# links[(땅A, 땅B)] = 거리   예) links[((0,0), (0,1))] = 1
links = {}

# 지금 어떤 화면인지:
# "setup"(지도 크기 정하기) / "edit"(편집) / "sim"(시뮬레이션) / "result"(순위표) / "path"(길 보기)
mode = "setup"

# 지도 크기 정하기 화면에서 쓰는 값들
size_text = "5*5"         # 입력 중인 지도 크기
setup_message = ""        # 잘못 입력했을 때 보여 줄 글

# 카메라: 지도가 화면보다 클 때, 지도의 어느 부분을 보고 있는지
camera_x, camera_y = 0, 0
dragging = False          # 마우스 휠 버튼을 누른 채 끌고 있는지

# 편집 화면에서 쓰는 값들
menu_cell = None          # 오른쪽 클릭 메뉴가 열린 땅 (없으면 None)
menu_buttons = []         # 메뉴 안의 버튼들 [(글자, 할일, 사각형), ...]
connect_from = None       # "연결" 중일 때 출발 땅
input_link = None         # 거리를 입력 중인 연결선
input_text = ""           # 입력 중인 글자
message = "땅을 왼쪽 클릭해서 활성화해 보세요."

# 시뮬레이션에서 쓰는 값들
routes = []               # 찾은 모든 길
sim_index = 0             # 지금 보여주는 길 번호
sim_step = 0              # 그 길에서 몇 번째 땅으로 가는 중인지
robot_pos = [0.0, 0.0]    # 로봇의 지도 위 위치 (카메라와 상관없는 위치)
robot_angle = 0           # 로봇이 바라보는 방향(회전 각도)
wait_timer = 0            # 길 하나가 끝나고 잠깐 쉬는 시간

# 순위표 / 길 보기 화면에서 쓰는 값들
ranking = []              # 순위대로 정렬된 길 목록
scroll = 0                # 순위표 스크롤 위치
chosen_route = None       # "길 보기"로 고른 길


# ---------------------------------------------------------------------
# 4. 작은 도우미 함수들
# ---------------------------------------------------------------------
# ※ 위치에는 두 종류가 있어요.
#   - 지도 위치 : 지도 왼쪽 위를 기준으로 한 위치 (카메라가 움직여도 그대로)
#   - 화면 위치 : 실제 창에 그려지는 위치 = 지도 위치 - 카메라 위치
def cell_map_center(cell):
    """땅 (줄, 칸) 의 가운데 '지도 위치'"""
    row, col = cell
    x = GRID_X + col * (CELL + GAP) + CELL // 2
    y = GRID_Y + row * (CELL + GAP) + CELL // 2
    return (x, y)


def to_screen(pos):
    """지도 위치 -> 화면 위치"""
    return (pos[0] - camera_x, pos[1] - camera_y)


def cell_center(cell):
    """땅 (줄, 칸) 의 가운데 '화면 위치'"""
    return to_screen(cell_map_center(cell))


def cell_rect(cell):
    """땅 (줄, 칸) 이 화면에서 차지하는 사각형"""
    rect = pygame.Rect(0, 0, CELL, CELL)
    rect.center = cell_center(cell)
    return rect


def cell_name(cell):
    """(0,0) -> 'A1' 처럼 사람이 읽기 쉬운 이름으로 바꾸기"""
    row, col = cell
    return LETTERS[col] + str(row + 1)


def cell_at(pos):
    """마우스 위치에 있는 땅을 찾기 (없으면 None)"""
    if not VIEW.collidepoint(pos):          # 지도 영역 밖이면 땅이 아님
        return None
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if cell_rect((row, col)).collidepoint(pos):
                return (row, col)
    return None


def make_map(cols, rows):
    """정한 크기로 빈 지도 만들기"""
    global GRID_COLS, GRID_ROWS, CELL, GAP, active, camera_x, camera_y
    GRID_COLS, GRID_ROWS = cols, rows

    # 땅 크기 정하기
    if use_scroll():
        CELL = 100        # 큰 지도: 땅은 원래 크기, 화면은 일부만 보임
    else:
        # 작은 지도: 지도 전체가 화면(VIEW)에 들어가도록 땅 크기를 줄임
        step_w = (VIEW.width - GRID_X - 20) / cols    # 한 칸(땅+간격)이 쓸 수 있는 가로 길이
        step_h = (VIEW.height - GRID_Y - 20) / rows   # 한 칸이 쓸 수 있는 세로 길이
        CELL = min(100, int(min(step_w, step_h) / 1.24))
    GAP = int(CELL * 0.24)
    load_map_images()     # 땅 크기가 바뀌었으니 그림 크기도 다시 맞춤

    active = [[False] * cols for _ in range(rows)]
    roles.clear()
    links.clear()
    camera_x, camera_y = 0, 0


def use_scroll():
    """가로나 세로가 SCROLL_SIZE(10) 이상이면 '일부만 보이기 + 끌어서 이동'을 씀"""
    return GRID_COLS >= SCROLL_SIZE or GRID_ROWS >= SCROLL_SIZE


def move_camera(dx, dy):
    """카메라를 움직이되, 지도 밖으로 너무 나가지 않게 막기"""
    global camera_x, camera_y
    map_w = GRID_X + GRID_COLS * (CELL + GAP) + 20   # 지도 전체 가로 길이
    map_h = GRID_Y + GRID_ROWS * (CELL + GAP) + 20   # 지도 전체 세로 길이
    max_x = max(0, map_w - VIEW.width)
    max_y = max(0, map_h - VIEW.height)
    camera_x = max(0, min(max_x, camera_x + dx))
    camera_y = max(0, min(max_y, camera_y + dy))


def focus_on(cell):
    """cell 이 지도 영역 가운데에 오도록 카메라 옮기기"""
    x, y = cell_center(cell)
    move_camera(x - VIEW.centerx, y - VIEW.centery)


def link_key(a, b):
    """두 땅의 순서와 상관없이 같은 연결로 보이도록 정렬"""
    return tuple(sorted([a, b]))


def find_role(role_name):
    """출발점/도착점이 있는 땅 찾기"""
    for cell, role in roles.items():
        if role == role_name:
            return cell
    return None


def distance_to_line(p, a, b):
    """점 p 에서 선분 a-b 까지의 거리"""
    px, py = p
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))        # 선분 밖으로 나가지 않게
    nearest_x, nearest_y = ax + t * dx, ay + t * dy
    return math.hypot(px - nearest_x, py - nearest_y)


def link_at(pos):
    """마우스 위치에 있는 연결선 찾기 (없으면 None)"""
    if not VIEW.collidepoint(pos):
        return None
    for key in links:
        a, b = cell_center(key[0]), cell_center(key[1])
        middle = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        # 1) 가운데 거리 숫자 동그라미를 눌렀을 때
        if math.hypot(pos[0] - middle[0], pos[1] - middle[1]) <= 14:
            return key
        # 2) 땅 위가 아닌 곳에서 선 가까이를 눌렀을 때
        if cell_at(pos) is None and distance_to_line(pos, a, b) <= 7:
            return key
    return None


def number_text(value):
    """1.0 -> '1', 2.5 -> '2.5'"""
    return f"{value:g}"


def can_start():
    return find_role("start") is not None and find_role("end") is not None


# ---------------------------------------------------------------------
# 5. 그리기 함수들
# ---------------------------------------------------------------------
def draw_text(text, font, color, pos, center=False):
    image = font.render(text, True, color)
    rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
    screen.blit(image, rect)


def draw_grid():
    """격자(땅, 장애물, 출발점, 도착점)와 줄/칸 이름 그리기
    ※ 지도 영역(VIEW) 밖으로는 그려지지 않도록 set_clip 으로 잘라냅니다.
      지도를 다 그린 뒤에는 end_map_drawing() 을 불러 잘라내기를 끕니다."""
    screen.set_clip(VIEW)
    for col in range(GRID_COLS):
        x = cell_center((0, col))[0]
        draw_text(LETTERS[col], FONT, GRAY, (x, GRID_Y - 20 - camera_y), center=True)
    for row in range(GRID_ROWS):
        y = cell_center((row, 0))[1]
        draw_text(str(row + 1), FONT, GRAY, (GRID_X - 25 - camera_x, y), center=True)

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cell = (row, col)
            rect = cell_rect(cell)
            if not rect.colliderect(VIEW):   # 화면에 안 보이는 땅은 건너뛰기
                continue
            image = place_img if active[row][col] else place_off_img
            screen.blit(image, image.get_rect(center=rect.center))

            role = roles.get(cell)
            if role == "hole":
                screen.blit(hole_img, hole_img.get_rect(center=rect.center))
            elif role == "start":
                screen.blit(start_img, start_img.get_rect(center=rect.center))
            elif role == "end":
                screen.blit(end_img, end_img.get_rect(center=rect.center))


def end_map_drawing():
    """지도 그리기를 끝내고, 오른쪽 안내 영역과 나눔선 그리기"""
    screen.set_clip(None)
    pygame.draw.line(screen, GRAY, (VIEW.right, 0), (VIEW.right, HEIGHT), 1)
    if use_scroll():
        draw_text("휠 버튼을 누른 채 끌기: 화면 이동", FONT_SMALL, GRAY, (690, 20))


def draw_link(key, color, width=5):
    """연결선 하나와 그 가운데에 거리 숫자 그리기"""
    a, b = cell_center(key[0]), cell_center(key[1])
    pygame.draw.line(screen, color, a, b, width)
    middle = ((a[0] + b[0]) // 2, (a[1] + b[1]) // 2)
    pygame.draw.circle(screen, (20, 20, 30), middle, 13)
    pygame.draw.circle(screen, color, middle, 13, 2)
    draw_text(number_text(links[key]), FONT_SMALL, WHITE, middle, center=True)


def draw_all_links():
    for key in links:
        draw_link(key, LINE_COLOR)


def draw_robot():
    image = pygame.transform.rotate(robot_img, robot_angle)
    x, y = to_screen(robot_pos)          # 로봇 위치는 지도 위치라서 화면 위치로 바꿈
    screen.blit(image, image.get_rect(center=(int(x), int(y))))


def draw_menu():
    """오른쪽 클릭 메뉴 그리기"""
    mouse = pygame.mouse.get_pos()
    for text, action, rect in menu_buttons:
        color = (80, 90, 120) if rect.collidepoint(mouse) else (50, 55, 75)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, WHITE, rect, 1)
        draw_text(text, FONT_SMALL, WHITE, rect.center, center=True)


def draw_input_box():
    """거리 입력 창 그리기"""
    box = pygame.Rect(0, 0, 420, 170)
    box.center = (WIDTH // 2, HEIGHT // 2)
    pygame.draw.rect(screen, (45, 50, 70), box, border_radius=12)
    pygame.draw.rect(screen, WHITE, box, 2, border_radius=12)
    name = cell_name(input_link[0]) + " - " + cell_name(input_link[1])
    draw_text(f"[{name}] 거리를 입력하세요", FONT, WHITE, (box.centerx, box.y + 30), center=True)
    field = pygame.Rect(box.x + 60, box.y + 60, 300, 44)
    pygame.draw.rect(screen, WHITE, field, border_radius=6)
    draw_text(input_text + "|", FONT, (0, 0, 0), (field.x + 10, field.y + 8))
    draw_text("Enter: 확인    Esc: 취소", FONT_SMALL, GRAY, (box.centerx, box.y + 135), center=True)


def draw_edit_screen():
    draw_grid()
    draw_all_links()

    # 연결 중이면 출발 땅에서 마우스까지 점선 느낌의 선
    if connect_from is not None:
        pygame.draw.line(screen, PATH_COLOR, cell_center(connect_from), pygame.mouse.get_pos(), 2)
    end_map_drawing()

    # 오른쪽 안내 영역
    screen.blit(go_img if can_start() else go_off_img, go_rect)
    screen.blit(random_img, random_rect)
    help_lines = [
        "[ 사용 방법 ]",
        "랜덤 버튼: 지도를 무작위로 만들기",
        "땅 왼쪽 클릭: 활성화 / 비활성화",
        "땅 오른쪽 클릭: 메뉴 열기",
        "   장애물 / 연결 / 출발점 / 도착점",
        "연결선 왼쪽 클릭: 연결 해제",
        "연결선 오른쪽 클릭: 거리 입력",
        "(거리를 안 넣으면 1)",
        "",
        "출발점과 도착점이 있으면",
        "시작 버튼이 켜집니다.",
    ]
    for i, line in enumerate(help_lines):
        draw_text(line, FONT_SMALL, WHITE, (690, 260 + i * 26))

    draw_text(message, FONT_SMALL, PATH_COLOR, (690, 570))

    if menu_cell is not None:
        draw_menu()
    if input_link is not None:
        draw_input_box()


def draw_sim_screen():
    draw_grid()
    draw_all_links()

    # 지금 탐색 중인 길을 노란색으로 표시
    route = routes[sim_index]["path"]
    for i in range(sim_step):
        pygame.draw.line(screen, PATH_COLOR, cell_center(route[i]), cell_center(route[i + 1]), 7)
    draw_robot()
    end_map_drawing()

    draw_text("시뮬레이션 중...", FONT_BIG, WHITE, (690, 80))
    draw_text(f"길 {sim_index + 1} / {len(routes)} 탐색 중", FONT, WHITE, (690, 140))
    draw_text("스페이스바: 건너뛰기", FONT_SMALL, GRAY, (690, 180))


def row_y(index):
    """순위표에서 index 번째 줄의 y 위치"""
    return 150 + index * 50 - scroll


def view_button_rect(index):
    return view_img.get_rect(midleft=(860, row_y(index) + 20))


def draw_result_screen():
    draw_text("순위표", FONT_BIG, WHITE, (40, 25))
    ok_count = sum(1 for r in ranking if r["ok"])
    draw_text(f"탐색한 길 {len(ranking)}개  /  도착 가능한 길 {ok_count}개", FONT, GRAY, (180, 35))
    if len(ranking) >= MAX_ROUTES:
        draw_text(f"(길이 너무 많아서 {MAX_ROUTES}개까지만 탐색했어요)", FONT_SMALL, FAIL_COLOR, (180, 68))

    # 제목 줄
    headers = [("순위", 40), ("경로", 120), ("이동 가능 여부", 625), ("거리", 785)]
    for text, x in headers:
        draw_text(text, FONT, PATH_COLOR, (x, 100))
    pygame.draw.line(screen, GRAY, (30, 135), (WIDTH - 30, 135), 1)

    # 표 내용 (표 영역 밖은 그리지 않도록 잘라내기)
    screen.set_clip(pygame.Rect(0, 140, WIDTH, HEIGHT - 240))
    rank = 0
    for i, route in enumerate(ranking):
        y = row_y(i)
        if route["ok"]:
            rank += 1
            rank_text, ok_text, color = f"{rank}위", "가능", OK_COLOR
            dist_text = number_text(route["dist"])
        else:
            rank_text, ok_text, color = "-", "불가능", FAIL_COLOR
            dist_text = "-"

        path_text = " → ".join(cell_name(c) for c in route["path"])
        # 너무 길면 '이동 가능 여부' 칸을 침범하지 않게 뒤를 잘라서 "..." 붙이기
        if FONT_SMALL.size(path_text)[0] > 480:
            while FONT_SMALL.size(path_text + " ...")[0] > 480:
                path_text = path_text[:-1]
            path_text += " ..."

        draw_text(rank_text, FONT, color, (40, y + 8))
        draw_text(path_text, FONT_SMALL, WHITE, (120, y + 10))
        draw_text(ok_text, FONT, color, (660, y + 8))
        draw_text(dist_text, FONT, color, (790, y + 8))
        screen.blit(view_img, view_button_rect(i))
    screen.set_clip(None)

    if len(ranking) > 9:
        draw_text("마우스 휠로 스크롤", FONT_SMALL, GRAY, (40, HEIGHT - 60))
    screen.blit(back_img, back_rect)


def draw_path_screen():
    draw_grid()
    route = chosen_route["path"]
    # 고른 길의 연결선만 그리기
    for i in range(len(route) - 1):
        draw_link(link_key(route[i], route[i + 1]), PATH_COLOR, 7)
    # 몇 번째로 밟는 땅인지 번호 표시
    for i, cell in enumerate(route):
        rect = cell_rect(cell)
        pygame.draw.circle(screen, (20, 20, 30), (rect.x + 16, rect.y + 16), 13)
        draw_text(str(i + 1), FONT_SMALL, WHITE, (rect.x + 16, rect.y + 16), center=True)
    draw_robot()
    end_map_drawing()

    draw_text("선택한 길", FONT_BIG, WHITE, (690, 80))
    if chosen_route["ok"]:
        draw_text("도착 가능", FONT, OK_COLOR, (690, 140))
        draw_text(f"거리: {number_text(chosen_route['dist'])}", FONT, WHITE, (690, 175))
    else:
        draw_text("도착 불가능 (막힌 길)", FONT, FAIL_COLOR, (690, 140))
    draw_text(f"밟은 땅: {len(route)}칸", FONT, WHITE, (690, 210))
    screen.blit(back_img, back_rect)


# ---------------------------------------------------------------------
# 6. 편집 화면 동작 (땅 활성화, 메뉴, 연결, 거리 입력)
# ---------------------------------------------------------------------
def open_menu(cell, pos):
    """오른쪽 클릭 메뉴 만들기"""
    global menu_cell, menu_buttons
    menu_cell = cell
    role = roles.get(cell)
    items = [
        ("장애물 제거" if role == "hole" else "장애물 설치", "hole"),
        ("연결", "connect"),
        ("출발점 해제" if role == "start" else "출발점 지정", "start"),
        ("도착점 해제" if role == "end" else "도착점 지정", "end"),
    ]
    menu_buttons = []
    x, y = pos
    x = min(x, WIDTH - 140)                  # 화면 밖으로 나가지 않게
    y = min(y, HEIGHT - 36 * len(items))
    for i, (text, action) in enumerate(items):
        menu_buttons.append((text, action, pygame.Rect(x, y + i * 36, 140, 36)))


def do_menu_action(action):
    """메뉴에서 고른 일을 실행"""
    global connect_from, message
    cell = menu_cell

    if action == "connect":
        connect_from = cell
        message = f"{cell_name(cell)} 과 연결할 땅을 왼쪽 클릭하세요."
        return

    # 장애물 / 출발점 / 도착점 : 이미 그 역할이면 해제, 아니면 지정
    if roles.get(cell) == action:
        del roles[cell]
        message = f"{cell_name(cell)} 의 표시를 지웠습니다."
        return

    # 출발점과 도착점은 지도에 하나만! -> 원래 있던 것을 지움
    if action in ("start", "end"):
        old = find_role(action)
        if old is not None:
            del roles[old]
    roles[cell] = action
    names = {"hole": "장애물", "start": "출발점", "end": "도착점"}
    message = f"{cell_name(cell)} 에 {names[action]}을(를) 놓았습니다."


def deactivate(cell):
    """땅을 비활성화하면 그 땅의 표시와 연결선도 함께 사라짐"""
    row, col = cell
    active[row][col] = False
    roles.pop(cell, None)
    for key in list(links):
        if cell in key:
            del links[key]


def handle_edit_event(event):
    global menu_cell, connect_from, input_link, input_text, message

    # --- 거리 입력 창이 열려 있을 때는 키보드만 받음 ---
    if input_link is not None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                try:
                    value = float(input_text)
                    if value > 0:
                        links[input_link] = value
                        message = f"거리를 {number_text(value)}(으)로 정했습니다."
                    else:
                        message = "거리는 0보다 커야 합니다."
                except ValueError:
                    message = "숫자만 입력할 수 있습니다."
                input_link = None
            elif event.key == pygame.K_ESCAPE:
                input_link = None
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            elif event.unicode in "0123456789." and event.unicode != "" and len(input_text) < 6:
                input_text += event.unicode
        return

    if event.type != pygame.MOUSEBUTTONDOWN or event.button not in (1, 3):
        return
    pos = event.pos
    left = event.button == 1

    # --- 메뉴가 열려 있을 때 ---
    if menu_cell is not None:
        if left:
            for text, action, rect in menu_buttons:
                if rect.collidepoint(pos):
                    do_menu_action(action)
        menu_cell = None   # 메뉴 바깥을 눌러도 메뉴는 닫힘
        return

    # --- "연결" 중일 때: 왼쪽 클릭한 땅과 연결 ---
    if connect_from is not None:
        target = cell_at(pos)
        if left and target is not None and target != connect_from and active[target[0]][target[1]]:
            key = link_key(connect_from, target)
            if key not in links:
                links[key] = 1          # 거리를 입력하지 않으면 1
            message = f"{cell_name(key[0])} - {cell_name(key[1])} 연결 완료!"
        else:
            message = "연결을 취소했습니다."
        connect_from = None
        return

    # --- 시작 버튼 ---
    if left and go_rect.collidepoint(pos) and can_start():
        start_simulation()
        return

    # --- 랜덤 버튼 ---
    if left and random_rect.collidepoint(pos):
        make_random_map()
        message = "랜덤 지도를 만들었습니다!"
        return

    # --- 연결선 클릭 ---
    key = link_at(pos)
    if key is not None:
        if left:
            del links[key]
            message = "연결을 해제했습니다."
        else:
            input_link = key
            input_text = ""
        return

    # --- 땅 클릭 ---
    cell = cell_at(pos)
    if cell is None:
        return
    row, col = cell
    if left:
        if active[row][col]:
            deactivate(cell)
            message = f"{cell_name(cell)} 을(를) 비활성화했습니다."
        else:
            active[row][col] = True
            message = f"{cell_name(cell)} 을(를) 활성화했습니다."
    elif active[row][col]:
        open_menu(cell, pos)


# ---------------------------------------------------------------------
# 7. 길 찾기 (모든 길을 가 보기) - 깊이 우선 탐색(DFS)
# ---------------------------------------------------------------------
def neighbors(cell):
    """cell 과 선으로 연결된 땅들과 그 거리 목록"""
    result = []
    for (a, b), dist in links.items():
        if a == cell:
            result.append((b, dist))
        elif b == cell:
            result.append((a, dist))
    return result


def find_all_routes():
    """출발점에서 갈 수 있는 모든 길을 찾습니다.
    - 도착점에 닿으면 '성공한 길'
    - 더 갈 곳이 없으면 '막힌 길'
    - 한 번 밟은 땅은 다시 밟지 않습니다.
    - 길이 너무 많으면 MAX_ROUTES 개까지만 찾습니다.
    """
    start = find_role("start")
    end = find_role("end")
    found = []

    def explore(cell, path, dist):
        if len(found) >= MAX_ROUTES:                      # 충분히 많이 찾았으면 그만
            return
        if cell == end:                                   # 도착!
            found.append({"path": list(path), "dist": dist, "ok": True})
            return
        moved = False
        for next_cell, d in neighbors(cell):
            if next_cell in path:                         # 이미 밟은 땅
                continue
            if roles.get(next_cell) == "hole":            # 장애물
                continue
            moved = True
            path.append(next_cell)                        # 한 칸 가 보고
            explore(next_cell, path, dist + d)            # 거기서 또 탐색
            path.pop()                                    # 돌아오기
        if not moved:                                     # 더 갈 곳이 없음
            found.append({"path": list(path), "dist": dist, "ok": False})

    explore(start, [start], 0)
    return found


# ---------------------------------------------------------------------
# 7-1. 랜덤 지도 만들기
# ---------------------------------------------------------------------
def all_cells():
    return [(row, col) for row in range(GRID_ROWS) for col in range(GRID_COLS)]


def side_neighbors(cell):
    """위/아래/왼쪽/오른쪽 이웃 땅 (지도 밖은 빼고)"""
    row, col = cell
    result = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        r, c = row + dr, col + dc
        if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
            result.append((r, c))
    return result


def add_random_link(a, b):
    """두 땅을 활성화하고 랜덤 거리(1~5)로 연결"""
    active[a[0]][a[1]] = True
    active[b[0]][b[1]] = True
    links[link_key(a, b)] = random.randint(1, 5)


def make_random_map():
    """랜덤으로 길을 만들고 장애물을 설치합니다.
    1) 출발점과 도착점을 무작위로 고르고, 둘을 잇는 '큰길'을 만든다 (그래서 항상 도착 가능!)
    2) 큰길에서 곁가지 길을 여기저기 뻗는다
    3) 이미 있는 땅끼리 몇 군데 더 이어서 돌아가는 길(고리)을 만든다
    4) 큰길이 아닌 땅 몇 곳에 장애물을 놓는다
    """
    global camera_x, camera_y
    # 지도 비우기 (크기는 그대로)
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            active[row][col] = False
    roles.clear()
    links.clear()
    camera_x, camera_y = 0, 0

    cells = all_cells()
    total = len(cells)

    # 1) 출발점, 도착점, 그리고 둘을 잇는 큰길
    start, end = random.sample(cells, 2)
    # 도착점까지 가려면 가로로 몇 칸, 세로로 몇 칸 가야 하는지 계산해서
    # 그 이동들을 섞으면 구불구불한 큰길이 됨
    dr = 1 if end[0] > start[0] else -1
    dc = 1 if end[1] > start[1] else -1
    moves = [(dr, 0)] * abs(end[0] - start[0]) + [(0, dc)] * abs(end[1] - start[1])
    random.shuffle(moves)
    road = [start]
    for mr, mc in moves:
        last = road[-1]
        road.append((last[0] + mr, last[1] + mc))
    for a, b in zip(road, road[1:]):
        add_random_link(a, b)
    active[start[0]][start[1]] = True

    # 2) 곁가지: 활성화된 땅 옆의 빈 땅을 하나씩 붙여 나감
    for _ in range(total // 2):
        here = random.choice([c for c in cells if active[c[0]][c[1]]])
        there = random.choice(side_neighbors(here))
        if not active[there[0]][there[1]]:
            add_random_link(here, there)

    # 3) 고리: 이웃한 활성화된 땅인데 아직 연결이 없으면 몇 군데 연결
    for _ in range(max(3, total // 8)):
        here = random.choice([c for c in cells if active[c[0]][c[1]]])
        there = random.choice(side_neighbors(here))
        if active[there[0]][there[1]] and link_key(here, there) not in links:
            add_random_link(here, there)

    # 4) 장애물: 큰길이 아닌 활성화된 땅 중 약 20%
    others = [c for c in cells if active[c[0]][c[1]] and c not in road]
    for cell in random.sample(others, len(others) // 5):
        roles[cell] = "hole"

    roles[start] = "start"
    roles[end] = "end"


def start_simulation():
    global mode, routes, sim_index
    routes = find_all_routes()
    sim_index = 0
    start_route()
    focus_on(find_role("start"))      # 출발점이 화면 가운데 오도록
    mode = "sim"


def start_route():
    """sim_index 번째 길을 처음부터 시작"""
    global sim_step, robot_pos, wait_timer
    first = routes[sim_index]["path"][0]
    robot_pos = list(cell_map_center(first))
    sim_step = 0
    wait_timer = 0


def update_simulation():
    """매 프레임마다 로봇을 조금씩 움직임"""
    global sim_step, sim_index, robot_angle, wait_timer
    route = routes[sim_index]["path"]

    if sim_step < len(route) - 1:
        # 다음 땅을 향해 이동
        tx, ty = cell_map_center(route[sim_step + 1])
        dx, dy = tx - robot_pos[0], ty - robot_pos[1]
        distance = math.hypot(dx, dy)
        # 로봇 그림은 왼쪽이 앞이므로 180도를 빼서 방향을 맞춤
        robot_angle = math.degrees(math.atan2(-dy, dx)) - 180
        if distance <= ROBOT_SPEED:
            robot_pos[0], robot_pos[1] = tx, ty
            sim_step += 1
        else:
            robot_pos[0] += dx / distance * ROBOT_SPEED
            robot_pos[1] += dy / distance * ROBOT_SPEED
        follow_robot()
    else:
        # 길 끝에 도착 -> 잠깐 쉬었다가 다음 길
        wait_timer += 1
        if wait_timer > 30:
            sim_index += 1
            if sim_index < len(routes):
                start_route()
            else:
                show_result()


def follow_robot():
    """로봇이 화면 가장자리로 가면 카메라가 따라감 (끌고 있는 중에는 따라가지 않음)"""
    if dragging:
        return
    x, y = to_screen(robot_pos)
    safe = VIEW.inflate(-200, -200)      # 이 안쪽에 로봇이 있으면 그대로 둠
    dx = dy = 0
    if x < safe.left:
        dx = x - safe.left
    elif x > safe.right:
        dx = x - safe.right
    if y < safe.top:
        dy = y - safe.top
    elif y > safe.bottom:
        dy = y - safe.bottom
    move_camera(dx, dy)


def show_result():
    """순위표 만들기: 도착 가능한 길 먼저, 그 안에서는 거리가 짧은 순서"""
    global mode, ranking, scroll
    ranking = sorted(routes, key=lambda r: (not r["ok"], r["dist"], len(r["path"])))
    scroll = 0
    mode = "result"


# ---------------------------------------------------------------------
# 8. 순위표 / 길 보기 화면 동작
# ---------------------------------------------------------------------
def handle_result_event(event):
    global mode, scroll, chosen_route, robot_pos, robot_angle
    if event.type == pygame.MOUSEWHEEL:
        max_scroll = max(0, len(ranking) * 50 - (HEIGHT - 260))
        scroll = max(0, min(max_scroll, scroll - event.y * 30))
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if back_rect.collidepoint(event.pos):
            mode = "edit"
            return
        if not (140 <= event.pos[1] <= HEIGHT - 100):   # 표 영역 밖
            return
        for i, route in enumerate(ranking):
            if view_button_rect(i).collidepoint(event.pos):
                chosen_route = route
                path = route["path"]
                robot_pos = list(cell_map_center(path[-1]))   # 로봇은 길 끝에 세움
                focus_on(path[-1])
                if len(path) > 1:
                    (x1, y1), (x2, y2) = cell_center(path[-2]), cell_center(path[-1])
                    robot_angle = math.degrees(math.atan2(-(y2 - y1), x2 - x1)) - 180
                mode = "path"


def handle_path_event(event):
    global mode
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if back_rect.collidepoint(event.pos):
            mode = "result"


# ---------------------------------------------------------------------
# 9. 지도 크기 정하기 화면 (프로그램을 켜면 가장 먼저 나옴)
# ---------------------------------------------------------------------
setup_go_rect = go_img.get_rect(center=(WIDTH // 2, 470))


def draw_setup_screen():
    draw_text("격자지도에서 이동경로 최소화", FONT_BIG, WHITE, (WIDTH // 2, 140), center=True)
    draw_text("지도 크기를  가로 * 세로  로 입력하세요", FONT, WHITE, (WIDTH // 2, 240), center=True)
    draw_text(f"예) 5*5,  10*8   (가로·세로 각각 2 ~ {MAX_SIZE})", FONT_SMALL, GRAY,
              (WIDTH // 2, 275), center=True)

    field = pygame.Rect(0, 0, 260, 54)
    field.center = (WIDTH // 2, 345)
    pygame.draw.rect(screen, WHITE, field, border_radius=8)
    draw_text(size_text + "|", FONT_BIG, (0, 0, 0), field.center, center=True)

    draw_text(setup_message, FONT_SMALL, FAIL_COLOR, (WIDTH // 2, 395), center=True)
    screen.blit(go_img, setup_go_rect)
    draw_text("Enter 키를 눌러도 시작합니다.", FONT_SMALL, GRAY, (WIDTH // 2, 540), center=True)


def read_size(text):
    """'10*8' 같은 글자를 (가로, 세로) 숫자로 바꾸기. 잘못되면 None"""
    text = text.replace("x", "*").replace("X", "*").replace(" ", "")
    parts = text.split("*")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        return None
    cols, rows = int(parts[0]), int(parts[1])
    if not (2 <= cols <= MAX_SIZE and 2 <= rows <= MAX_SIZE):
        return None
    return cols, rows


def finish_setup():
    global mode, setup_message, message
    size = read_size(size_text)
    if size is None:
        setup_message = f"형식이 틀렸어요. 예) 10*8  (2 ~ {MAX_SIZE} 사이 숫자)"
        return
    make_map(size[0], size[1])
    message = f"{size[0]} x {size[1]} 지도를 만들었습니다!"
    mode = "edit"


def handle_setup_event(event):
    global size_text
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_RETURN:
            finish_setup()
        elif event.key == pygame.K_BACKSPACE:
            size_text = size_text[:-1]
        elif event.unicode != "" and event.unicode in "0123456789*xX" and len(size_text) < 7:
            size_text += event.unicode
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if setup_go_rect.collidepoint(event.pos):
            finish_setup()


def handle_drag_event(event):
    """마우스 휠 버튼(가운데 버튼)을 누른 채 끌면 지도 화면이 움직임"""
    global dragging
    if not use_scroll():          # 작은 지도는 다 보이니까 움직일 필요 없음
        return
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2 and VIEW.collidepoint(event.pos):
        dragging = True
    elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
        dragging = False
    elif event.type == pygame.MOUSEMOTION and dragging:
        # 마우스를 오른쪽으로 끌면 지도가 오른쪽으로 따라오도록 (카메라는 반대로)
        move_camera(-event.rel[0], -event.rel[1])


# ---------------------------------------------------------------------
# 10. 메인 반복문 (게임의 심장)
# ---------------------------------------------------------------------
running = True
while running:
    # (1) 입력 처리
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            continue
        if mode in ("edit", "sim", "path"):   # 지도가 보이는 화면에서는 끌어서 이동 가능
            handle_drag_event(event)

        if mode == "setup":
            handle_setup_event(event)
        elif mode == "edit":
            handle_edit_event(event)
        elif mode == "sim":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                show_result()
        elif mode == "result":
            handle_result_event(event)
        elif mode == "path":
            handle_path_event(event)

    # (2) 움직임 계산
    if mode == "sim":
        update_simulation()

    # (3) 화면 그리기
    screen.fill(BG_COLOR)
    if mode == "setup":
        draw_setup_screen()
    elif mode == "edit":
        draw_edit_screen()
    elif mode == "sim":
        draw_sim_screen()
    elif mode == "result":
        draw_result_screen()
    elif mode == "path":
        draw_path_screen()

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
