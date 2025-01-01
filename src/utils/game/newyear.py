import pygame
import random

# 初始化 Pygame
pygame.init()

# 设置屏幕大小
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))

# 设置标题
pygame.display.set_caption("新年快乐, Moro! (来自 Neo)")

# 定义颜色
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)

colors = [red, green, blue, white] # 多彩的祝福语

# 定义字体
font_size = 30
font = pygame.font.SysFont(None, font_size) # 使用系统默认字体

# 定义祝福语列表
greetings = [
    "新年快乐!",
    "万事如意!",
    "心想事成!",
    "Happy New Year!",
    "2025 更美好!",
    "福星高照!",
    "恭喜发财!",
    "身体健康!",
    "学业进步!", # 给Moro的特别祝福
    "天天开心!"
]

# 定义祝福语对象
class Greeting:
    def __init__(self, text, color, x, y, speed):
        self.text = text
        self.color = color
        self.x = x
        self.y = y
        self.speed = speed
        self.text_surface = font.render(self.text, True, self.color)

    def move(self):
        self.y += self.speed
        if self.y > screen_height:
            self.y = -font_size
            self.x = random.randint(0, screen_width - self.text_surface.get_width())
            self.speed = random.randint(1, 5)
            self.text_surface = font.render(random.choice(greetings), True, random.choice(colors))

    def draw(self):
        screen.blit(self.text_surface, (self.x, self.y))

# 创建祝福语对象列表
greeting_objects = []
for _ in range(20):  # 屏幕上同时显示的祝福语数量
    text = random.choice(greetings)
    color = random.choice(colors)
    x = random.randint(0, screen_width)
    y = random.randint(-screen_height, 0) # 初始位置在屏幕上方
    speed = random.randint(1, 5)
    greeting_objects.append(Greeting(text, color, x, y, speed))

# 游戏循环
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 清空屏幕
    screen.fill(black)

    # 移动和绘制祝福语
    for greeting in greeting_objects:
        greeting.move()
        greeting.draw()

    # 更新屏幕
    pygame.display.flip()

    # 控制帧率
    clock.tick(30)  # 每秒 30 帧

# 退出 Pygame
pygame.quit()