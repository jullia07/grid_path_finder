# make_objects.py
# 원래 없던 오브젝트(그림)를 만들어 주는 작은 프로그램입니다.
# 한 번만 실행하면 view_butten_object.png(길 보기 버튼) 파일이 생깁니다.
#   실행 방법:  python make_objects.py

import pygame

pygame.init()

# 1) 그림을 그릴 투명한 도화지 만들기 (가로 400, 세로 140)
image = pygame.Surface((400, 140), pygame.SRCALPHA)

# 2) 파란색 둥근 버튼 그리기 (테두리 -> 안쪽 순서)
pygame.draw.rect(image, (10, 60, 160), (0, 0, 400, 140), border_radius=45)
pygame.draw.rect(image, (40, 120, 230), (10, 10, 380, 120), border_radius=38)

# 3) 가운데에 "길 보기" 글자 쓰기
font = pygame.font.SysFont("malgungothic", 70, bold=True)
text = font.render("길 보기", True, (255, 255, 255))
image.blit(text, text.get_rect(center=(200, 70)))

# 4) 파일로 저장
pygame.image.save(image, "view_butten_object.png")
print("view_butten_object.png 를 만들었습니다!")
