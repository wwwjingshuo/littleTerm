# -*- coding: utf-8 -*-
"""
显示在ssd1306上的贪吃蛇游戏
运行后，可以通过按任意按钮启动游戏。
默认情况下，蛇初始时从左到右移动。游戏的目的是收集尽可能多的水果，水果将随机放置。
随着每吃一个水果，蛇就会变得更长。
当蛇撞到墙上或它自己时，游戏结束，显示Gameover。
此时可通过按任意按钮，将游戏还原为起始值，然后触摸按钮即可再次启动游戏。
"""

# todo 要求：
#  1.在屏幕上输出现在的等级
#  等级要求：当蛇为一定值时，每次吃一定的水果会让他速度增加，到一定值停止增加
#  当蛇长为10的时候，每吃一个水果，其运动延时减少2，到运动延时降低为5时停止


import random   # 引入随机数库
import time     # 引入时间库
from machine import Pin, I2C
import ssd1306

SCREEN_WIDTH = 128
SCREEN_HEIGHT = 64  # 定义屏幕高度

# 上下左右引脚, 通过上拉电阻设为高电平【可ctrl点击Pin了解详情】
# 参数： 1. 选择所对应的IO口  2. 设置引脚是输入还是输出  3. 设置是否有电阻
# http://www.1zlab.com/wiki/micropython-esp32/pin/
# 使用上拉电阻将该引脚置高电平
UP_PIN = Pin(5, Pin.IN, Pin.PULL_UP)
DOWN_PIN = Pin(14 , Pin.IN, Pin.PULL_UP)
LEFT_PIN = Pin(4, Pin.IN, Pin.PULL_UP)
RIGHT_PIN = Pin(15, Pin.IN, Pin.PULL_UP)

# snake config
SNAKE_PIECE_SIZE = 3  # 蛇的每一格占用3*3个像素
MAX_SNAKE_LENGTH = 150  # 蛇的最长长度
MAP_SIZE_X = 20  # 活动范围
MAP_SIZE_Y = 20
START_SNAKE_SIZE = 3  # 初始长度
SNAKE_MOVE_DELAY = 30  # 移动延时


# game config
class State(object):
    START = 0
    RUNNING = 1
    GAMEOVER = 2

# https://www.runoob.com/python/python-func-classmethod.html
# 【@classmethod】有什么用 https://blog.csdn.net/qq_23981335/article/details/103798741

    @classmethod
    def setter(cls, state):
        if state == cls.START:
            return cls.START
        elif state == cls.RUNNING:
            return cls.RUNNING
        elif state == cls.GAMEOVER:
            return cls.GAMEOVER


class Direction(object):
    # 设定顺序
    UP = 0
    LEFT = 1
    DOWN = 2
    RIGHT = 3

    @classmethod
    def setter(cls, dirc):
        if dirc == cls.UP:
            return cls.UP
        elif dirc == cls.DOWN:
            return cls.DOWN
        elif dirc == cls.LEFT:
            return cls.LEFT
        elif dirc == cls.RIGHT:
            return cls.RIGHT

# https://docs.micropython.org/en/latest/library/machine.I2C.html
i2c = I2C(0)

# 初始化屏幕
screen = ssd1306.SSD1306_I2C(SCREEN_WIDTH, SCREEN_HEIGHT, I2C(0))


################ Snake 功能实现 ###################
class Snake(object):
    # 初始化函数
    def __init__(self):
        self.snake = []  # 初始位置[（x1,y1）,(x2,y2),...]一个元组列表
        self.fruit = []  # 水果，[x,y]
        self.snake_length = START_SNAKE_SIZE # 蛇的长度
        self.direction = Direction.RIGHT  # 当前前进方向
        self.new_direction = Direction.RIGHT  # 用户按键后的前进方向
        self.game_state = None # 游戏当前模式
        self.display = screen   # 显示设备初始化
        self.setup_game()   #初始化游戏

    def setup_game(self):
        """初始化游戏"""
        self.game_state = State.START   # 将游戏设置为开始状态
        self.reset_snake()  # 重新设置蛇的长度
        self.generate_fruit()   # 随机生成水果
        self.display.fill(0)    # 用指定的颜色填充整个FrameBuffer  0代表黑色
        self.draw_map() # 绘制地图
        self.show_score()   # 显示分数
        self.show_press_to_start()  # 显示提示信息
        self.display.show() # 显示内容

    def reset_snake(self):
        """重设蛇的位置"""
        self.snake = []  # 重置
        self.snake_length = START_SNAKE_SIZE
        for i in range(self.snake_length):
            self.snake.append((MAP_SIZE_X // 2 - i, MAP_SIZE_Y // 2))   # 将蛇移到屏幕中间

    def check_fruit(self):
        """检测蛇是否吃到水果，能否继续吃水果"""
        if self.snake[0][0] == self.fruit[0] and self.snake[0][1] == self.fruit[1]:
            if self.snake_length + 1 < MAX_SNAKE_LENGTH:
                self.snake_length += 1
                # 吃到水果后，将蛇增加一格
                self.snake.insert(0, (self.fruit[0], self.fruit[1]))
            self.generate_fruit()

    def generate_fruit(self):
        """随机生成水果位置，注意不能生成在蛇身上"""
        while True:
            self.fruit = [random.randint(1, MAP_SIZE_X - 1), random.randint(1, MAP_SIZE_Y - 1)]
            #【tuple】使用方法 https://www.runoob.com/python/att-tuple-tuple.html
            fruit = tuple(self.fruit)
            if fruit in self.snake:
                # 生成在蛇身上
                continue
            else:
                print('fruit: ', self.fruit)
                break

    @staticmethod
    def button_press():
        """是否有按键按下"""
        for pin in UP_PIN, DOWN_PIN, LEFT_PIN, RIGHT_PIN:
            if pin.value() == 0:  # 低电平表示按下
                return True
        return False

    def read_direction(self):
        """读取新的按键方向，不能与当前方向相反"""
        for direction, pin in enumerate((UP_PIN, LEFT_PIN, DOWN_PIN, RIGHT_PIN)):
            if pin.value() == 0 and not (direction == (self.direction + 2) % 4):
                self.new_direction = Direction.setter(direction)
                return

    def collection_check(self, x, y):
        """检查蛇社否撞到墙或者（x,y）位置"""
        for i in self.snake:
            if x == i[0] and y == i[1]:
                return True
        if x < 0 or y < 0 or x >= MAP_SIZE_X or y >= MAP_SIZE_Y:
            return True
        return False

    def move_snake(self):
        """按照方向键移动蛇，返回能否继续移动的布尔值"""
        x, y = self.snake[0]
        new_x, new_y = x, y

        if self.direction == Direction.UP:
            new_y -= 1
        elif self.direction == Direction.DOWN:
            new_y += 1
        elif self.direction == Direction.LEFT:
            new_x -= 1
        elif self.direction == Direction.RIGHT:
            new_x += 1

        if self.collection_check(new_x, new_y):  # 不能继续移动
            return False

        self.snake.pop()  # 去除最后一个位置
        self.snake.insert(0, (new_x, new_y))  # 在开头添加新位置
        return True  # 能继续移动

    def draw_map(self):
        """绘制地图区域: 蛇、水果、边界"""
        offset_map_x = SCREEN_WIDTH - SNAKE_PIECE_SIZE * MAP_SIZE_X - 2
        offset_map_y = 2

        # 绘制水果
        self.display.rect(self.fruit[0] * SNAKE_PIECE_SIZE + offset_map_x,
                          self.fruit[1] * SNAKE_PIECE_SIZE + offset_map_y,
                          SNAKE_PIECE_SIZE, SNAKE_PIECE_SIZE, 1)
        # 绘制地图边界, 边界占一个像素，但是绘制时在内侧留一个像素，当蛇头部到达内部一个像素时，即判定为碰撞
        self.display.rect(offset_map_x - 2,
                          0,
                          SNAKE_PIECE_SIZE * MAP_SIZE_X + 4,
                          SNAKE_PIECE_SIZE * MAP_SIZE_Y + 4, 1)
        # 绘制蛇
        for x, y in self.snake:
            self.display.fill_rect(x * SNAKE_PIECE_SIZE + offset_map_x,
                                   y * SNAKE_PIECE_SIZE + offset_map_y,
                                   SNAKE_PIECE_SIZE,
                                   SNAKE_PIECE_SIZE, 1)

    def show_score(self):
        """显示得分"""
        score = self.snake_length - START_SNAKE_SIZE
        # 【text】方法直接ctrl点击即可
        self.display.text('Score:%d' % score, 0, 2, 1)

    def show_press_to_start(self):
        """提示按任意键开始游戏"""
        self.display.text('Press', 0, 16, 1)
        self.display.text('button', 0, 26, 1)
        self.display.text('start!', 0, 36, 1)

    def show_game_over(self):
        """显示游戏结束"""
        self.display.text('Game', 0, 30, 1)
        self.display.text('Over!', 0, 40, 1)


#################  循环运行程序  ##################
if __name__ == '__main__':
    # print('******** Start ********')
    snake = Snake() # 定义一条蛇
    move_time = 0   # 移动次数
    while True:
        if snake.game_state == State.START:
            if Snake.button_press():
                snake.game_state = State.RUNNING

        elif snake.game_state == State.RUNNING:
            move_time += 1
            snake.read_direction()
            if move_time >= SNAKE_MOVE_DELAY:
                snake.direction = snake.new_direction
                snake.display.fill(0)
                if not snake.move_snake():
                    snake.game_state = State.GAMEOVER
                    snake.show_game_over()
                    time.sleep(1)
                snake.draw_map()
                snake.show_score()
                snake.display.show()
                snake.check_fruit()
                move_time = 0

        elif snake.game_state == State.GAMEOVER:
            if Snake.button_press():
                time.sleep_ms(500)
                snake.setup_game()
                print('******** new game ********')
                snake.game_state = State.START

        time.sleep_ms(20)

