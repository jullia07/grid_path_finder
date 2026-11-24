# make_objects.py
# 원래 없던 오브젝트(그림)를 만들어 주는 작은 프로그램입니다.
# 한 번만 실행하면 아래 버튼 그림 파일들이 생깁니다.
#   - view_butten_object.png   : 길 보기 버튼 (파란색)
#   - random_butten_object.png : 랜덤 버튼 (보라색)
#   실행 방법:  python make_objects.py

import pygame

pygame.init()
font = pygame.font.SysFont("malgungothic", 70, bold=True)


def make_button(filename, text, border_color, inside_color):
    """둥근 버튼 그림을 만들어서 파일로 저장"""
    # 1) 그림을 그릴 투명한 도화지 만들기 (가로 400, 세로 140)
    image = pygame.Surface((400, 140), pygame.SRCALPHA)

    # 2) 둥근 버튼 그리기 (테두리 -> 안쪽 순서)
    pygame.draw.rect(image, border_color, (0, 0, 400, 140), border_radius=45)
    pygame.draw.rect(image, inside_color, (10, 10, 380, 120), border_radius=38)

    # 3) 가운데에 글자 쓰기
    label = font.render(text, True, (255, 255, 255))
    image.blit(label, label.get_rect(center=(200, 70)))

    # 4) 파일로 저장
    pygame.image.save(image, filename)
    print(filename, "를 만들었습니다!")


make_button("view_butten_object.png", "길 보기", (10, 60, 160), (40, 120, 230))
make_button("random_butten_object.png", "랜덤", (80, 30, 140), (150, 70, 220))
