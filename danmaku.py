import pygame
import random
import math
from enum import Enum

# 初期化
pygame.init()

# 画面設定
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("弾幕ゲー - ランダム図形降下")

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# 図形の種類
class ShapeType(Enum):
    CIRCLE = 1
    RECTANGLE = 2
    TRIANGLE = 3
    DIAMOND = 4

# 発狂パターンの種類
class FrenzyType(Enum):
    CIRCLE_BURST = 1      # 円形弾幕
    GIANT_FALLING = 2     # 巨大落下弾
    HOMING_SQUARE = 3     # 追尾四角弾
    FLASH = 4             # ビーム型
    NET_FLASH = 5         # Flashの亜種（ネット状ビーム）
    RUSH = 6              # ラッシュ型（新規追加）
    PETAFLARE = 7         # ペタフレア（新規追加）
    REVENGE = 8           # リベンジ（新通常発狂）
    MINI_BORDER = 9       # ミニボーダー（新規追加）
    ALTER = 10            # ALTER（新規追加）
    DOUBLE = 11           # DOUBLE（新規追加）

class Shape:
    def __init__(self, x, y, shape_type, color, speed):
        self.x = x
        self.y = y
        self.shape_type = shape_type
        self.color = color
        self.speed = speed
        self.size = random.randint(15, 35)
        self.rotation = 0
        self.rotation_speed = random.uniform(-3, 3)
        # 追加: デフォルト値
        self.vx: float | None = None
        self.vy: float | None = None
        self._shrink = False
        self._shrink_rate = 1.0
        
    def update(self):
        """図形の位置と回転を更新"""
        # vx, vyがあればそちらを優先
        if hasattr(self, 'vx') and hasattr(self, 'vy') and self.vx is not None and self.vy is not None:
            self.x += self.vx
            self.y += self.vy
        else:
            self.y += self.speed
        self.rotation += self.rotation_speed
        # _shrinkフラグがあれば縮小
        if hasattr(self, '_shrink') and self._shrink:
            rate = getattr(self, '_shrink_rate', 1)
            self.size = max(2, self.size - rate)
        
    def draw(self, surface):
        """図形を描画"""
        if self.shape_type == ShapeType.CIRCLE:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
            
        elif self.shape_type == ShapeType.RECTANGLE:
            rect = pygame.Rect(self.x - self.size, self.y - self.size, 
                             self.size * 2, self.size * 2)
            pygame.draw.rect(surface, self.color, rect)
            
        elif self.shape_type == ShapeType.TRIANGLE:
            points = [
                (self.x, self.y - self.size),
                (self.x - self.size, self.y + self.size),
                (self.x + self.size, self.y + self.size)
            ]
            # 回転を適用
            rotated_points = []
            for point in points:
                rotated_x = (point[0] - self.x) * math.cos(math.radians(self.rotation)) - \
                           (point[1] - self.y) * math.sin(math.radians(self.rotation)) + self.x
                rotated_y = (point[0] - self.x) * math.sin(math.radians(self.rotation)) + \
                           (point[1] - self.y) * math.cos(math.radians(self.rotation)) + self.y
                rotated_points.append((rotated_x, rotated_y))
            pygame.draw.polygon(surface, self.color, rotated_points)
            
        elif self.shape_type == ShapeType.DIAMOND:
            points = [
                (self.x, self.y - self.size),
                (self.x + self.size, self.y),
                (self.x, self.y + self.size),
                (self.x - self.size, self.y)
            ]
            # 回転を適用
            rotated_points = []
            for point in points:
                rotated_x = (point[0] - self.x) * math.cos(math.radians(self.rotation)) - \
                           (point[1] - self.y) * math.sin(math.radians(self.rotation)) + self.x
                rotated_y = (point[0] - self.x) * math.sin(math.radians(self.rotation)) + \
                           (point[1] - self.y) * math.cos(math.radians(self.rotation)) + self.y
                rotated_points.append((rotated_x, rotated_y))
            pygame.draw.polygon(surface, self.color, rotated_points)
    
    def is_off_screen(self):
        """画面外に出たかどうかを判定（上下とも±300pxマージン）"""
        margin = 300
        return self.y > SCREEN_HEIGHT + margin or self.y < -margin

# 特殊弾幕クラス
class FrenzyBullet:
    def __init__(self, x, y, target_x=None, target_y=None, bullet_type=FrenzyType.CIRCLE_BURST):
        self.x = x
        self.y = y
        self.bullet_type = bullet_type
        self.size = 5  # 基本サイズ
        self.speed = 3
        self.color = YELLOW  # 任意の色タプルを許容
        self.shrink_speed = 0  # ペタフレア用
        
        # 追尾弾用の目標座標
        if target_x is not None and target_y is not None:
            self.target_x = target_x
            self.target_y = target_y
            dx = target_x - x
            dy = target_y - y
            self.angle = math.atan2(dy, dx)
            self.speed = 8
        
        # ペタフレア用初期化
        if bullet_type == FrenzyType.PETAFLARE:
            self.size = random.randint(40, 60) * 3
            self.speed = 6.25 * 2 / 3
            self.shrink_speed = (random.uniform(2.5, 4.0) / 3) * 2 / 3
        
    def update(self):
        """弾幕の位置を更新"""
        if self.bullet_type == FrenzyType.HOMING_SQUARE:
            self.x += math.cos(self.angle) * self.speed
            self.y += math.sin(self.angle) * self.speed
        elif self.bullet_type == FrenzyType.CIRCLE_BURST or self.bullet_type == FrenzyType.PETAFLARE:
            if hasattr(self, 'angle'):
                self.x += math.cos(self.angle) * self.speed
                self.y += math.sin(self.angle) * self.speed
            else:
                self.y += self.speed
            if self.bullet_type == FrenzyType.PETAFLARE:
                self.size -= self.shrink_speed
        else:
            self.y += self.speed
            
    def draw(self, surface):
        """弾幕を描画"""
        if self.bullet_type == FrenzyType.HOMING_SQUARE:
            # 追尾四角弾
            rect = pygame.Rect(self.x - self.size, self.y - self.size, 
                             self.size * 2, self.size * 2)
            pygame.draw.rect(surface, self.color, rect)
        else:
            # 円形弾幕と巨大落下弾
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), int(self.size))
    
    def is_off_screen(self):
        """画面外に出たかどうかを判定"""
        if self.bullet_type == FrenzyType.PETAFLARE:
            return (self.y > SCREEN_HEIGHT + self.size or self.size <= 5)
        return (self.y > SCREEN_HEIGHT + self.size or 
                self.y < -self.size or 
                self.x < -self.size or 
                self.x > SCREEN_WIDTH + self.size)

class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 50
        self.width = 10  # 小さく
        self.height = 10  # 小さく
        self.speed = 5
        
    def update(self, keys):
        """プレイヤーの移動を更新（上下左右）"""
        if keys[pygame.K_LEFT] and self.x > self.width // 2:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < SCREEN_WIDTH - self.width // 2:
            self.x += self.speed
        if keys[pygame.K_UP] and self.y > self.height // 2:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y < SCREEN_HEIGHT - self.height // 2:
            self.y += self.speed
            
    def draw(self, surface):
        """プレイヤーを描画"""
        pygame.draw.rect(surface, WHITE, 
                        (self.x - self.width // 2, self.y - self.height // 2, 
                         self.width, self.height))
        
    def get_rect(self):
        """プレイヤーの矩形を取得（衝突判定用）"""
        return pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, 
                          self.width, self.height)

class Game:
    def __init__(self):
        self.shapes = []
        self.frenzy_bullets = []  # 発狂弾幕
        self.frenzy_flash_beams = []  # FLASHビーム型弾幕
        self.player = Player()
        self.score = 0
        self.lives = 3
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.shape_spawn_timer = 0
        # 難易度ごとの出現間隔
        self.spawn_delays = [30, 20, 13, 8, 6]  # Easy, Normal, Hard, Lunatic, Unfair
        self.min_spawn_delay = 5
        self.max_spawn_delay = 100
        self.score_per_shape = 10
        self.min_score_per_shape = 1
        self.max_score_per_shape = 100
        self.difficulty = 1  # 1: Easy, 2: Normal, 3: Hard, 4: Lunatic, 5: Unfair
        self.difficulty_labels = ["Easy", "Normal", "Hard", "Lunatic", "Unfair"]
        # 初期値を難易度に応じてセット
        self.shape_spawn_delay = self.spawn_delays[self.difficulty - 1]
        self.frenzy_mode = False
        self.frenzy_timer = 0
        self.frenzy_duration = 780  # 13秒 (60fps * 13)
        self.frenzy_interval = 900  # 15秒 (60fps * 15)
        self.frenzy_interval_timer = 0
        self.current_frenzy_type = None
        self.frenzy_spawn_timer = 0
        self.frenzy_spawn_delay = 5  # 発狂弾幕の生成間隔
        self.homing_circle_timer = 0  # ホーミング発狂用タイマー
        # FLASH用
        self.flash_beam_spawn_timer = 0
        self.flash_beam_spawn_delay = 60  # 1秒ごとに生成（初期値、難易度で調整）
        self.homing_square_spawn_delays = [60, 45, 30, 20, 10]  # Easy, Normal, Hard, Lunatic, Unfair
        self.flash_additional_shape_timer = 0  # 追加弾幕用タイマー
        self.flash_additional_shape_interval = 180  # 3秒ごと（60fps * 3）
        self.rush_mode_timer = 0
        self.rush_mode_active = False
        self.rush_mode_duration = 180  # 3秒発狂
        self.rush_mode_rest = 180      # 3秒休憩
        self.frenzy_count = 0  # 発狂突破回数
        self.boss_frenzy_trigger = 4  # 4回突破でボス弾幕
        self.boss_frenzy_mode = False
        self.boss_frenzy_timer = 0
        self.boss_frenzy_duration = 2160  # 36秒間（60fps換算）
        self.boss_patterns = ["storm", "smork", "border"]  # gravityを除外
        self.unused_boss_patterns = self.boss_patterns.copy()  # 未選択ボス弾幕リスト
        self.storm_phase = 1
        self.storm_phase_timer = 0
        self.storm_phase_duration = 720  # 12秒ごとに形態変化
        self.border_phase = 1
        self.border_phase_timer = 0
        self.border_phase_duration = 360  # 6形態で各6秒（例）
        self.side_triangle_timer = 0  # 両端三角形用タイマー
        self.side_triangle_interval = 120  # 2秒ごと（60fps * 2）
        self.extra_life_score = 1000
        self.next_extra_life_score = self.extra_life_score
        self.smork_phase = 1
        self.smork_phase_timer = 0
        self.smork_phase_duration = 720  # 12秒ごとに形態変化
        self.petaflare_spawn_timer = 0
        self.petaflare_spawn_delays = [72, 56, 40, 28, 20]  # 生成頻度1.25倍
        self.petaflare_yellow_timer = 0
        self.petaflare_yellow_intervals = [15, 12, 10, 8, 6]  # 難易度ごと
        self.rank = 0  # ランク値（発狂ごとに+1、ボスごとに+3）
        self.score_per_shape_timer = 0  # スコア自動加算用タイマー
        # gravity用
        self.gravity_phase = 1
        self.gravity_phase_timer = 0
        self.gravity_beam_timer = 0
        self.gravity_beam_side = 0  # 0:左, 1:右
        self.gravity_side_swap_timer = 0
        self.gravity_left_is_alter = True  # True:左ALTER/右通常, False:左通常/右ALTER
        # Gameクラス __init__ に追加
        self.requiem_ready = False
        self.requiem_warning = False
        self.requiem_warning_timer = 0
        self.requiem_started = False
        self.requiem_boss_left = 3
        self.requiem_phase = 1
        self.requiem_phase_timer = 0
        self.requiem_total_timer = 0
        
    def start_frenzy(self):
        """発狂モードを開始"""
        self.frenzy_mode = True
        self.frenzy_timer = 0
        # EasyのときはnetFlashとmini_borderを除外
        if self.difficulty == 1:
            available_types = [ft for ft in FrenzyType if ft not in (FrenzyType.NET_FLASH, FrenzyType.MINI_BORDER)]
            self.current_frenzy_type = random.choice(available_types)
        elif self.difficulty == 2:
            available_types = [ft for ft in FrenzyType if ft != FrenzyType.MINI_BORDER]
            self.current_frenzy_type = random.choice(available_types)
        else:
            self.current_frenzy_type = random.choice(list(FrenzyType))
        self.shapes.clear()
        self.frenzy_bullets.clear()
        self.frenzy_flash_beams.clear()
        print(f"発狂開始！パターン: {self.current_frenzy_type.name}")
        # GIANT_FALLINGの場合は発狂開始時に左右両端から超巨大弾を1発ずつ落とす
        if self.current_frenzy_type == FrenzyType.GIANT_FALLING:
            for side in [0, SCREEN_WIDTH]:
                bullet = FrenzyBullet(side, 50, bullet_type=FrenzyType.GIANT_FALLING)  # y座標を50に
                bullet.size = 250  # さらに巨大に
                bullet.speed = 1   # さらに遅く
                self.frenzy_bullets.append(bullet)
        # FLASHの場合、タイマー初期化
        if self.current_frenzy_type in [FrenzyType.FLASH, FrenzyType.NET_FLASH]:
            self.flash_beam_spawn_timer = 0
            self.flash_additional_shape_timer = 0
            self.flash_beam_active_count = 0
            if self.current_frenzy_type == FrenzyType.FLASH:
                self.flash_beam_spawn_delay = max(15, 60 - self.difficulty * 8)
            elif self.current_frenzy_type == FrenzyType.NET_FLASH:
                self.flash_beam_spawn_delay = 30  # 常に30フレームごとに1セット
        # ALTER発狂時はshape_spawn_delayを難易度に合わせて4倍に再設定
        if self.current_frenzy_type == FrenzyType.ALTER:
            self.shape_spawn_delay = self.spawn_delays[self.difficulty - 1] * 4
        elif self.current_frenzy_type == FrenzyType.DOUBLE:
            self.shape_spawn_delay = self.spawn_delays[self.difficulty - 1] * 8
        else:
            self.shape_spawn_delay = self.spawn_delays[self.difficulty - 1]
        self.rush_mode_timer = 0
        self.rush_mode_active = False

    def end_frenzy(self):
        """発狂モードを終了"""
        self.frenzy_mode = False
        self.current_frenzy_type = None
        # 発狂突破ボーナス
        self.score += 200 * self.difficulty
        self.frenzy_count += 1
        self.shapes.clear()
        self.frenzy_bullets.clear()
        self.frenzy_flash_beams.clear()
        print("発狂終了")
        # ランク加算
        self.rank += 1
        # shape_spawn_delayを難易度に応じてリセット
        self.shape_spawn_delay = self.spawn_delays[self.difficulty - 1]
        # ボス弾幕発動判定
        if self.frenzy_count >= self.boss_frenzy_trigger:
            self.boss_frenzy_mode = True
            self.frenzy_count = 0
            # 既存ボス3種を全て倒したらラスボスフラグ
            # if self.boss_patterns == [] or self.requiem_boss_left <= 0:
            #     self.requiem_ready = True
            #     self.requiem_warning = True
            #     self.requiem_warning_timer = 0
            #     self.shapes.clear()
            #     self.frenzy_bullets.clear()
            #     self.frenzy_flash_beams.clear()
            # else:
            self.start_boss_frenzy()
        
    def start_boss_frenzy(self):
        print("ボス弾幕開始！")
        self.boss_frenzy_mode = True
        self.boss_frenzy_timer = 0
        # 未選択リストからランダム選択、空ならリセット
        if not self.unused_boss_patterns:
            self.unused_boss_patterns = self.boss_patterns.copy()
        self.boss_pattern = random.choice(self.unused_boss_patterns)
        self.unused_boss_patterns.remove(self.boss_pattern)
        # storm用
        self.storm_phase = 1
        self.storm_phase_timer = 0
        # smork用
        self.smork_phase = 1
        self.smork_phase_timer = 0
        # border用
        if self.boss_pattern == "border" and self.difficulty >= 4:
            self.border_phase = 2  # Lunatic以上は2形態目から
        else:
            self.border_phase = 1
        self.border_phase_timer = 0
        # 例として、開始時に全画面CircleBurstを1回発射
        center_x = SCREEN_WIDTH // 2
        center_y = -10
        for i in range(24):
            angle = 2 * math.pi * i / 24
            bullet = FrenzyBullet(center_x, center_y, bullet_type=FrenzyType.CIRCLE_BURST)
            bullet.angle = angle
            bullet.speed = 6
            bullet.size = 6
            self.frenzy_bullets.append(bullet)
        # ボス発狂開始時にランク+3
        self.rank += 3
        # gravity用
        self.gravity_phase = 1
        self.gravity_phase_timer = 0
        self.gravity_beam_timer = 0
        self.gravity_beam_side = 0  # 0:左, 1:右
        # start_boss_frenzyの最後に追加
        if self.boss_pattern in ["storm", "smork", "border"]:
            self.requiem_boss_left = max(0, self.requiem_boss_left - 1)
            # 使い切ったらリストから除外
            if self.boss_pattern in self.boss_patterns:
                self.boss_patterns.remove(self.boss_pattern)

    def spawn_frenzy_bullets(self):
        """発狂弾幕を生成"""
        if not self.frenzy_mode:
            return
        
        if self.current_frenzy_type == FrenzyType.CIRCLE_BURST:
            # 円形弾幕：上中央から上半分のランダムな角度で発射
            center_x = SCREEN_WIDTH // 2
            center_y = -10
            num_bullets = self.difficulty  # 難易度と同じ数（難易度1なら1発）
            for i in range(num_bullets):
                angle = random.uniform(0, 2 * math.pi)
                bullet = FrenzyBullet(center_x, center_y, bullet_type=FrenzyType.CIRCLE_BURST)
                bullet.angle = angle
                bullet.speed = 8
                bullet.size = 3
                self.frenzy_bullets.append(bullet)
        elif self.current_frenzy_type == FrenzyType.GIANT_FALLING:
            # 発狂中は1フレームごとに左右真ん中から小型球を発射
            for side in [0, SCREEN_WIDTH]:
                center_y = SCREEN_HEIGHT // 2
                num_bullets = self.difficulty  # 難易度分
                for i in range(num_bullets):
                    angle = random.uniform(0, 2 * math.pi)
                    bullet = FrenzyBullet(side, center_y, bullet_type=FrenzyType.CIRCLE_BURST)
                    bullet.angle = angle
                    bullet.speed = 2  # 少しゆっくり目
                    bullet.size = 5  # 小型
                    self.frenzy_bullets.append(bullet)
        elif self.current_frenzy_type == FrenzyType.HOMING_SQUARE:
            # 追尾四角弾：プレイヤーの位置に突進
            bullet = FrenzyBullet(
                random.choice([0, SCREEN_WIDTH]), 
                random.randint(0, SCREEN_HEIGHT // 2),
                self.player.x, self.player.y,
                FrenzyType.HOMING_SQUARE
            )
            self.frenzy_bullets.append(bullet)
            # 2秒ごとに難易度×6発の小型球を上中央から全方位ランダムに発射
            if self.frenzy_timer % 120 == 0:
                center_x = SCREEN_WIDTH // 2
                center_y = -10
                num_bullets = self.difficulty * 6
                for i in range(num_bullets):
                    angle = random.uniform(0, 2 * math.pi)
                    b = FrenzyBullet(center_x, center_y, bullet_type=FrenzyType.CIRCLE_BURST)
                    b.angle = angle
                    b.speed = 6
                    b.size = 3
                    self.frenzy_bullets.append(b)
        elif self.current_frenzy_type == FrenzyType.FLASH:
            num_beams = self.difficulty + random.randint(0, self.difficulty)
            beam_width = 5
            warning_time = 40
            active_time = 2
            color_warning = (255, 255, 100)
            color_active = (255, 220, 0)
            for _ in range(num_beams):
                edge = random.choice(['top', 'bottom', 'left', 'right'])
                if edge == 'top':
                    x0 = random.randint(0, SCREEN_WIDTH)
                    y0 = -10
                elif edge == 'bottom':
                    x0 = random.randint(0, SCREEN_WIDTH)
                    y0 = SCREEN_HEIGHT
                elif edge == 'left':
                    x0 = 0
                    y0 = random.randint(0, SCREEN_HEIGHT)
                else:
                    x0 = SCREEN_WIDTH
                    y0 = random.randint(0, SCREEN_HEIGHT)
                tx = random.randint(0, SCREEN_WIDTH)
                ty = random.randint(0, SCREEN_HEIGHT)
                beam = FlashBeam((x0, y0), (tx, ty), beam_width, warning_time, active_time, color_warning, color_active)
                self.frenzy_flash_beams.append(beam)
        elif self.current_frenzy_type == FrenzyType.NET_FLASH:
            num_beams = 1  # 常に1本に固定
            beam_width = 5
            warning_time = 80  # 猶予2倍
            active_time = 10   # 10フレーム照射
            color_warning = (200, 255, 255)
            color_active = (0, 200, 255)
            for _ in range(num_beams):
                edge = random.choice(['top', 'bottom', 'left', 'right'])
                if edge == 'top':
                    x0 = random.randint(0, SCREEN_WIDTH)
                    y0 = -10
                elif edge == 'bottom':
                    x0 = random.randint(0, SCREEN_WIDTH)
                    y0 = SCREEN_HEIGHT
                elif edge == 'left':
                    x0 = 0
                    y0 = random.randint(0, SCREEN_HEIGHT)
                else:
                    x0 = SCREEN_WIDTH
                    y0 = random.randint(0, SCREEN_HEIGHT)
                tx = random.randint(0, SCREEN_WIDTH)
                ty = random.randint(0, SCREEN_HEIGHT)
                beam = FlashBeam((x0, y0), (tx, ty), beam_width, warning_time, active_time, color_warning, color_active)
                self.frenzy_flash_beams.append(beam)
        elif self.current_frenzy_type == FrenzyType.RUSH:
            # Rush発狂時はrush_mode_activeがTrueのときのみ発射
            if not self.rush_mode_active:
                return
            positions = [
                (SCREEN_WIDTH // 2, 0),
                (0, 0),
                (SCREEN_WIDTH, 0)
            ]
            num_bullets = max(1, self.difficulty // 2)  # 難易度の半分、最低1発
            for pos in positions:
                for i in range(num_bullets):
                    angle = random.uniform(0, 2 * math.pi)
                    bullet = FrenzyBullet(pos[0], pos[1], bullet_type=FrenzyType.CIRCLE_BURST)
                    bullet.angle = angle
                    bullet.speed = 5  # 少し遅め
                    bullet.size = 3
                    self.frenzy_bullets.append(bullet)
        elif self.current_frenzy_type == FrenzyType.MINI_BORDER:
            # ミニボーダー弾幕（難易度ごとにphase指定）
            if self.difficulty == 3:  # Hard
                mini_phases = [1, 3, 4]
            elif self.difficulty == 4:  # Lunatic
                mini_phases = [1, 2, 4, 6]
            else:  # Unfair
                mini_phases = [1, 2, 3, 5, 6]
            mini_offsets = {1: 0, 2: 2, 3: 4, 4: 6, 5: 8, 6: 0}
            mini_bullets = {1: 12, 2: 15, 3: 20, 4: 10, 5: 24, 6: 12}
            mini_angles = {1: 30, 2: 24, 3: 18, 4: 36, 5: 15, 6: 30}
            def border_way_speed(p, base_speed):
                if self.difficulty <= 2:  # easy/normal
                    return 1, base_speed
                elif self.difficulty == 3:  # hard
                    if p == 2 or p == 5:
                        return 3, base_speed
                    elif p == 1 or p == 4 or p == 6:
                        return 3, base_speed
                    else:
                        return 1, base_speed
                elif self.difficulty == 4:  # lunatic
                    if p == 2:
                        return 5, base_speed
                    elif p == 1 or p == 4 or p == 6:
                        return 3, base_speed
                    else:
                        return 1, base_speed
                else:  # unfair
                    speed_up = 1.2 if p in [1,2,5] else 0
                    if p == 5:
                        return 3, base_speed + speed_up
                    elif p == 2:
                        return 3, base_speed + speed_up
                    elif p == 1:
                        return 3, base_speed + speed_up
                    elif p == 4 or p == 6:
                        return 3, base_speed
                    else:
                        return 1, base_speed
            for p in mini_phases:
                offset = mini_offsets[p]
                # interval分岐: unfairかつphase5のみ6フレーム、それ以外は従来通り
                if self.difficulty == 5 and p == 5:
                    interval = 6
                elif self.difficulty == 5 and p == 2:
                    interval = 6
                else:
                    interval = 6 if p == 6 else 12
                if (self.frenzy_timer - offset) % interval == 0:
                    center_x = SCREEN_WIDTH // 2
                    center_y = 0
                    n = mini_bullets[p]
                    angle_step = mini_angles[p]
                    if p == 1:
                        way, spd = border_way_speed(1, 5)
                        idx = ((self.frenzy_timer - offset) // interval) % n
                        angle = math.radians(idx * angle_step + ((self.frenzy_timer // interval) * (angle_step // 2)))
                        for da in [0] if way == 1 else [-15, 0, 15]:
                            a = angle + math.radians(da)
                            shape = Shape(center_x, center_y, ShapeType.TRIANGLE, YELLOW, spd)
                            shape.size = 24
                            shape.vx = float(math.cos(a) * spd)
                            shape.vy = float(math.sin(a) * spd)
                            self.shapes.append(shape)
                    elif p == 2:
                        way, spd = border_way_speed(2, 6)
                        idx = ((self.frenzy_timer - offset) // interval) % n
                        angle = math.radians(idx * angle_step + ((self.frenzy_timer // interval) * (angle_step // 2)))
                        if self.difficulty == 5 and way == 3 and p == 2:
                            # unfair専用7way
                            for da in [-36, -24, -12, 0, 12, 24, 36]:
                                a = angle + math.radians(da)
                                shape = Shape(center_x, center_y, ShapeType.CIRCLE, CYAN, spd)
                                shape.size = 8
                                shape.vx = float(math.cos(a) * spd)
                                shape.vy = float(math.sin(a) * spd)
                                self.shapes.append(shape)
                        elif way == 1:
                            a = angle
                            shape = Shape(center_x, center_y, ShapeType.CIRCLE, CYAN, spd)
                            shape.size = 8
                            shape.vx = float(math.cos(a) * spd)
                            shape.vy = float(math.sin(a) * spd)
                            self.shapes.append(shape)
                        else:
                            for da in [-12, 0, 12] if way == 3 else [-24, -12, 0, 12, 24]:
                                a = angle + math.radians(da)
                                shape = Shape(center_x, center_y, ShapeType.CIRCLE, CYAN, spd)
                                shape.size = 8
                                shape.vx = float(math.cos(a) * spd)
                                shape.vy = float(math.sin(a) * spd)
                                self.shapes.append(shape)
                    elif p == 3:
                        way, spd = border_way_speed(3, 4)
                        idx = ((self.frenzy_timer - offset) // interval) % n
                        angle = math.radians(idx * angle_step + ((self.frenzy_timer // interval) * (angle_step // 2)))
                        shape = Shape(center_x, center_y, ShapeType.CIRCLE, BLUE, 96)
                        shape.size = 96
                        shape.vx = math.cos(angle) * spd
                        shape.vy = math.sin(angle) * spd
                        shape._shrink = True
                        shape._shrink_rate = 1/3
                        self.shapes.append(shape)
                    elif p == 4:
                        way, spd = border_way_speed(4, 5)
                        idx = ((self.frenzy_timer - offset) // interval) % n
                        angle = math.radians(idx * angle_step + ((self.frenzy_timer // interval) * (angle_step // 2)))
                        for da in [0] if way == 1 else [-10, 0, 10]:
                            a = angle + math.radians(da)
                            shape = Shape(center_x, center_y, ShapeType.CIRCLE, PURPLE, spd)
                            shape.size = 16
                            shape.vx = math.cos(a) * spd
                            shape.vy = math.sin(a) * spd
                            self.shapes.append(shape)
                    elif p == 5:
                        way, spd = border_way_speed(5, 5)
                        idx = ((self.frenzy_timer - offset) // interval) % n
                        angle = math.radians(idx * angle_step + ((self.frenzy_timer // interval) * (angle_step // 2)))
                        for da in [0] if way == 1 else [-15, 0, 15]:
                            a = angle + math.radians(da)
                            shape = Shape(center_x, center_y, ShapeType.CIRCLE, GREEN, spd)
                            shape.size = 20
                            shape.vx = math.cos(a) * spd
                            shape.vy = math.sin(a) * spd
                            self.shapes.append(shape)
                    elif p == 6:
                        way, spd = border_way_speed(6, 7)
                        shot_count = ((self.frenzy_timer - offset) // interval)
                        base_angle = math.radians(270 - shot_count * 15)
                        for da in [0] if way == 1 else [-15, 0, 15]:
                            a = base_angle + math.radians(da)
                            shape = Shape(center_x, center_y, ShapeType.CIRCLE, WHITE, spd)
                            shape.size = 18
                            shape.vx = math.cos(a) * spd
                            shape.vy = math.sin(a) * spd
                            self.shapes.append(shape)
        elif self.current_frenzy_type == FrenzyType.ALTER:
            # ALTER発狂：3秒ごとにレーザーのみ
            if self.frenzy_timer % 180 == 0:
                for _ in range(self.difficulty):
                    x0 = random.randint(0, SCREEN_WIDTH)
                    y0 = SCREEN_HEIGHT + 10
                    tx = x0
                    ty = -10
                    beam = FlashBeam((x0, y0), (tx, ty), 5, 120, 60, (255, 180, 255), (255, 80, 255))
                    self.frenzy_flash_beams.append(beam)
        elif self.current_frenzy_type == FrenzyType.DOUBLE:
            # DOUBLE発狂：3秒ごとにレーザーのみ
            if self.frenzy_timer % 180 == 0:
                for _ in range(self.difficulty):
                    x0 = random.randint(0, SCREEN_WIDTH)
                    y0 = SCREEN_HEIGHT + 10
                    tx = x0
                    ty = -10
                    beam = FlashBeam((x0, y0), (tx, ty), 5, 120, 60, (255, 180, 255), (255, 80, 255))
                    self.frenzy_flash_beams.append(beam)
        elif self.current_frenzy_type == FrenzyType.REVENGE:
            # 通常より間隔を短縮（unfairで1フレーム、他も-1）
            revenge_mod = 1
            revenge_delay = max(1, self.spawn_delays[self.difficulty - 1] - revenge_mod)
            if not hasattr(self, 'revenge_shape_timer'):
                self.revenge_shape_timer = 0
            self.revenge_shape_timer += 1
            if self.revenge_shape_timer >= revenge_delay:
                shape_type = random.choice(list(ShapeType))
                color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, CYAN])
                x = random.randint(50, SCREEN_WIDTH - 50)
                speed = random.uniform(2, 6) + 1.0  # 弾速+1.0
                shape = Shape(x, -50, shape_type, color, speed)
                self.shapes.append(shape)
                self.revenge_shape_timer = 0
        elif self.current_frenzy_type == FrenzyType.PETAFLARE:
            # 小型黄色弾
            self.petaflare_yellow_timer += 1
            if self.petaflare_yellow_timer >= self.petaflare_yellow_intervals[self.difficulty - 1]:
                center_x = SCREEN_WIDTH // 2
                y = -10
                bullet = FrenzyBullet(center_x, y, bullet_type=FrenzyType.CIRCLE_BURST)
                bullet.size = 8
                bullet.speed = 5
                bullet.angle = random.uniform(0, 2 * math.pi)  # 毎回ランダムな方向
                self.frenzy_bullets.append(bullet)
                self.petaflare_yellow_timer = 0
        
    def spawn_shape(self):
        """新しい図形を生成"""
        if self.frenzy_mode:
            return  # 発狂中は通常弾幕を生成しない
        shape_type = random.choice(list(ShapeType))
        color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, CYAN])
        x = random.randint(50, SCREEN_WIDTH - 50)
        speed = random.uniform(2, 6) + self.rank * 0.1
        shape = Shape(x, -50, shape_type, color, speed)
        self.shapes.append(shape)
        # ランクに応じてボーナス弾幕（灰色三角形）を追加発射
        bonus_prob = min(1.0, self.rank * 0.02)
        if random.random() < bonus_prob:
            bonus_x = random.randint(50, SCREEN_WIDTH - 50)
            bonus_shape = Shape(bonus_x, -50, ShapeType.TRIANGLE, (180, 180, 180), speed)
            bonus_shape.size = 18
            self.shapes.append(bonus_shape)
        
    def update(self):
        """ゲーム状態を更新"""
        # ボス弾幕の管理
        if self.boss_frenzy_mode:
            self.boss_frenzy_timer += 1
            # stormパターンの形態管理
            if self.boss_pattern == "storm":
                self.storm_phase_timer += 1
                if self.storm_phase_timer >= self.storm_phase_duration:
                    self.storm_phase += 1
                    self.storm_phase_timer = 0
                    if self.storm_phase > 3:
                        self.storm_phase = 3  # 最終段階で固定
                # --- 各形態ごとの弾幕ロジック ---
                base_delay = self.spawn_delays[self.difficulty - 1]
                if self.difficulty == 5:
                    delay_mod = 1
                elif self.difficulty == 4:
                    delay_mod = 2
                else:
                    delay_mod = 3
                storm_delay = max(1, base_delay - delay_mod)
                if self.storm_phase == 1:
                    # 第一形態のみ図形降下のみ
                    self.shape_spawn_timer += 1
                    if self.shape_spawn_timer >= storm_delay:
                        shape_type = random.choice(list(ShapeType))
                        color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, CYAN])
                        x = random.randint(50, SCREEN_WIDTH - 50)
                        speed = random.uniform(2.5, 6.5)  # +0.5
                        shape = Shape(x, -50, shape_type, color, speed)
                        self.shapes.append(shape)
                        self.shape_spawn_timer = 0
                elif self.storm_phase == 2:
                    self.shape_spawn_timer += 1
                    if self.shape_spawn_timer >= storm_delay:
                        shape_type = random.choice(list(ShapeType))
                        color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, CYAN])
                        x = random.randint(50, SCREEN_WIDTH - 50)
                        speed = random.uniform(3.0, 7.0)  # +1.0
                        shape = Shape(x, -50, shape_type, color, speed)
                        self.shapes.append(shape)
                        self.shape_spawn_timer = 0
                    if self.storm_phase_timer % (storm_delay * 4) == 0:
                        center_x = SCREEN_WIDTH // 2
                        center_y = -10
                        num_bullets = self.difficulty
                        for i in range(num_bullets):
                            angle = random.uniform(0, 2 * math.pi)
                            bullet = FrenzyBullet(center_x, center_y, bullet_type=FrenzyType.CIRCLE_BURST)
                            bullet.angle = angle
                            bullet.speed = 8
                            bullet.size = 3
                            self.frenzy_bullets.append(bullet)
                elif self.storm_phase == 3:
                    self.shape_spawn_timer += 1
                    if self.shape_spawn_timer >= storm_delay:
                        shape_type = random.choice(list(ShapeType))
                        color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, CYAN])
                        x = random.randint(50, SCREEN_WIDTH - 50)
                        speed = random.uniform(3.5, 7.5)  # +1.5
                        shape = Shape(x, -50, shape_type, color, speed)
                        self.shapes.append(shape)
                        self.shape_spawn_timer = 0
                    if self.storm_phase_timer % (storm_delay * 4) == 0:
                        positions = [
                            (SCREEN_WIDTH // 2, 0),
                            (0, 0),
                            (SCREEN_WIDTH, 0)
                        ]
                        num_bullets = max(1, self.difficulty // 2)
                        for pos in positions:
                            for i in range(num_bullets):
                                angle = random.uniform(0, 2 * math.pi)
                                bullet = FrenzyBullet(pos[0], pos[1], bullet_type=FrenzyType.CIRCLE_BURST)
                                bullet.angle = angle
                                bullet.speed = 5
                                bullet.size = 3
                                self.frenzy_bullets.append(bullet)
            # smorkパターンの形態管理
            elif self.boss_pattern == "smork":
                self.smork_phase_timer += 1
                if self.smork_phase_timer >= self.smork_phase_duration:
                    self.smork_phase += 1
                    self.smork_phase_timer = 0
                    if self.smork_phase > 3:
                        self.smork_phase = 3  # 最終段階で固定
                # --- smork各形態の弾幕ロジック ---
                # 共通：rush（灰色、間隔3倍、弾速半分、休憩なし、6方向）
                rush_interval = self.spawn_delays[self.difficulty - 1] * 3
                rush_speed = 4.0  # 通常rushの半分
                if self.smork_phase >= 1:
                    if self.smork_phase_timer % rush_interval == 0:
                        positions_angles = [
                            ((0, 0), 0, math.pi / 2),              # 左上
                            ((SCREEN_WIDTH, 0), math.pi / 2, math.pi),  # 右上
                            ((0, SCREEN_HEIGHT), math.pi, 3 * math.pi / 2),  # 左下
                            ((SCREEN_WIDTH, SCREEN_HEIGHT), 3 * math.pi / 2, 2 * math.pi)  # 右下
                        ]
                        num_bullets = max(1, self.difficulty // 2)
                        for pos, angle_min, angle_max in positions_angles:
                            for i in range(num_bullets):
                                angle = random.uniform(angle_min, angle_max)
                                bullet = FrenzyBullet(pos[0], pos[1], bullet_type=FrenzyType.CIRCLE_BURST)
                                bullet.angle = angle
                                bullet.speed = rush_speed
                                bullet.size = 3
                                self.frenzy_bullets.append(bullet)
                # 第二形態：白Flash（猶予・間隔3倍、照射12倍、追加弾幕なし）
                if self.smork_phase >= 2:
                    # 3秒ごとに上端中央から円形弾幕
                    if self.smork_phase_timer % 180 == 0:
                        num_bullets = self.difficulty * 6 + 12
                        center_x = SCREEN_WIDTH // 2
                        center_y = -100
                        for i in range(num_bullets):
                            angle = 2 * math.pi * i / num_bullets
                            bullet = FrenzyBullet(center_x, center_y, bullet_type=FrenzyType.CIRCLE_BURST)
                            bullet.angle = angle
                            bullet.speed = 2.2  # やや遅め
                            bullet.size = 4     # やや大きめ
                            self.frenzy_bullets.append(bullet)
                    # 白Flash（レーザー）
                    flash_interval = self.spawn_delays[self.difficulty - 1] * 3 * 2  # 発生頻度を半減（2倍遅く）
                    flash_warning = 40 * 3
                    flash_active = 2 * 12
                    if self.smork_phase_timer % flash_interval == 0:
                        num_beams = 1
                        beam_width = 5
                        color_warning = (255, 255, 255)
                        color_active = (255, 255, 255)
                        edge = random.choice(['top', 'bottom', 'left', 'right'])
                        if edge == 'top':
                            x0 = random.randint(0, SCREEN_WIDTH)
                            y0 = -10
                        elif edge == 'bottom':
                            x0 = random.randint(0, SCREEN_WIDTH)
                            y0 = SCREEN_HEIGHT
                        elif edge == 'left':
                            x0 = 0
                            y0 = random.randint(0, SCREEN_HEIGHT)
                        else:
                            x0 = SCREEN_WIDTH
                            y0 = random.randint(0, SCREEN_HEIGHT)
                        tx = random.randint(0, SCREEN_WIDTH)
                        ty = random.randint(0, SCREEN_HEIGHT)
                        beam = FlashBeam((x0, y0), (tx, ty), beam_width, flash_warning, flash_active, color_warning, color_active)
                        self.frenzy_flash_beams.append(beam)
                # 第三形態：白HOMING_SQUARE（弾速半減・間隔2倍・easy仕様）
                if self.smork_phase == 3:
                    homing_interval = self.homing_square_spawn_delays[0] * 2  # easyの2倍
                    if self.smork_phase_timer % homing_interval == 0:
                        bullet = FrenzyBullet(
                            random.choice([0, SCREEN_WIDTH]),
                            random.randint(0, SCREEN_HEIGHT // 2),
                            self.player.x, self.player.y,
                            FrenzyType.HOMING_SQUARE
                        )
                        bullet.speed = 4  # easyの半分
                        self.frenzy_bullets.append(bullet)
            if self.boss_frenzy_timer >= self.boss_frenzy_duration:
                self.boss_frenzy_mode = False
                self.boss_frenzy_timer = 0
                print("ボス弾幕終了！")
                # --- 通常状態への復帰処理 ---
                self.frenzy_mode = False
                self.frenzy_interval_timer = self.frenzy_interval  # 即座に発狂再開
                self.shape_spawn_timer = 0
                self.storm_phase = 1
                self.storm_phase_timer = 0
                self.smork_phase = 1
                self.smork_phase_timer = 0
                self.current_frenzy_type = None
            # --- ここから下はボス弾幕中も常に動かす ---
            # 図形の更新
            for shape in self.shapes[:]:
                shape.update()
                if shape.is_off_screen():
                    self.shapes.remove(shape)
            # 発狂弾幕の更新
            for bullet in self.frenzy_bullets[:]:
                bullet.update()
                if bullet.is_off_screen():
                    self.frenzy_bullets.remove(bullet)
            # FLASHビームの更新
            for beam in self.frenzy_flash_beams[:]:
                prev_state = beam.state
                beam.update()
                if not beam.is_active():
                    self.frenzy_flash_beams.remove(beam)
            # プレイヤーの更新
            keys = pygame.key.get_pressed()
            self.player.update(keys)
            # 衝突判定
            self.check_collisions()
        # --- ここから下は通常発狂システム ---
        # 発狂システムの更新
        if self.frenzy_mode:
            self.frenzy_timer += 1
            if self.frenzy_timer >= self.frenzy_duration:
                self.end_frenzy()
            # ペタフレア弾幕生成
            if self.current_frenzy_type == FrenzyType.PETAFLARE:
                self.petaflare_spawn_timer += 1
                if self.petaflare_spawn_timer >= self.petaflare_spawn_delays[self.difficulty - 1]:
                    x = random.randint(60, SCREEN_WIDTH - 60)
                    y = -60
                    bullet = FrenzyBullet(x, y, bullet_type=FrenzyType.PETAFLARE)
                    bullet.angle = math.pi / 2  # 常に下方向
                    self.frenzy_bullets.append(bullet)
                    self.petaflare_spawn_timer = 0
                # 小型黄色弾
                self.petaflare_yellow_timer += 1
                if self.petaflare_yellow_timer >= self.petaflare_yellow_intervals[self.difficulty - 1]:
                    center_x = SCREEN_WIDTH // 2
                    y = -10
                    bullet = FrenzyBullet(center_x, y, bullet_type=FrenzyType.CIRCLE_BURST)
                    bullet.size = 8
                    bullet.speed = 5
                    bullet.angle = random.uniform(0, 2 * math.pi)  # 毎回ランダムな方向
                    self.frenzy_bullets.append(bullet)
                    self.petaflare_yellow_timer = 0
            # --- 新通常発狂：revenge ---
            if self.current_frenzy_type == FrenzyType.REVENGE:
                if not hasattr(self, 'revenge_shape_timer'):
                    self.revenge_shape_timer = 0
                self.revenge_shape_timer += 1
                # 通常より間隔を短縮（unfairで1フレーム、他も-1）
                revenge_mod = 1
                revenge_delay = max(1, self.spawn_delays[self.difficulty - 1] - revenge_mod)
                if self.revenge_shape_timer >= revenge_delay:
                    shape_type = random.choice(list(ShapeType))
                    color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, CYAN])
                    x = random.randint(50, SCREEN_WIDTH - 50)
                    speed = random.uniform(2, 6) + 1.0  # 弾速+1.0
                    shape = Shape(x, -50, shape_type, color, speed)
                    self.shapes.append(shape)
                    self.revenge_shape_timer = 0
        else:
            self.frenzy_interval_timer += 1
            if not self.requiem_started and self.frenzy_interval_timer >= self.frenzy_interval:
                self.start_frenzy()
                self.frenzy_interval_timer = 0
        # 両端三角形の生成（ノーマル以上のみ）
        if self.difficulty >= 2:
            self.side_triangle_timer += 1
            # ランクで降下間隔を短縮（最低10フレーム）
            interval = max(10, self.side_triangle_interval - self.rank * 2)
            if self.side_triangle_timer >= interval:
                size = 25  # 普通サイズ
                speed = random.uniform(2, 6)
                # 左端
                shape_left = Shape(25, -50, ShapeType.TRIANGLE, YELLOW, speed)
                shape_left.size = size
                self.shapes.append(shape_left)
                # 右端
                shape_right = Shape(SCREEN_WIDTH - 25, -50, ShapeType.TRIANGLE, YELLOW, speed)
                shape_right.size = size
                self.shapes.append(shape_right)
                self.side_triangle_timer = 0
        
        # HOMING_SQUARE発狂時の上からの円形弾
        if self.frenzy_mode and self.current_frenzy_type == FrenzyType.HOMING_SQUARE:
            self.homing_circle_timer += 1
            if self.homing_circle_timer >= 120:
                center_x = SCREEN_WIDTH // 2
                center_y = -100
                num_bullets = self.difficulty * 6
                for i in range(num_bullets):
                    angle = random.uniform(0, 2 * math.pi)
                    b = FrenzyBullet(center_x, center_y, bullet_type=FrenzyType.CIRCLE_BURST)
                    b.angle = angle
                    b.speed = 6
                    b.size = 3
                    self.frenzy_bullets.append(b)
                self.homing_circle_timer = 0
        else:
            self.homing_circle_timer = 0
        
        # 発狂弾幕の生成
        if self.frenzy_mode:
            self.frenzy_spawn_timer += 1
            if self.frenzy_spawn_timer >= self.frenzy_spawn_delay:
                if self.current_frenzy_type != FrenzyType.FLASH:
                    self.spawn_frenzy_bullets()
                self.frenzy_spawn_timer = 0
                # 円形弾幕の場合は15分の1秒ごとに生成
                if self.current_frenzy_type == FrenzyType.CIRCLE_BURST:
                    self.frenzy_spawn_delay = 4  # 15分の1秒（60fps ÷ 15 = 4フレーム）
                # 追尾弾の場合は難易度に応じて生成間隔を調整
                elif self.current_frenzy_type == FrenzyType.HOMING_SQUARE:
                    self.frenzy_spawn_delay = self.homing_square_spawn_delays[self.difficulty - 1]
                # 巨大落下弾の場合は3フレームごとに生成
                elif self.current_frenzy_type == FrenzyType.GIANT_FALLING:
                    self.frenzy_spawn_delay = 3  # 3フレームごと
                else:
                    self.frenzy_spawn_delay = 5  # その他の弾幕は高速生成
            # FLASHビームの生成タイミング
            if self.frenzy_mode and self.current_frenzy_type in [FrenzyType.FLASH, FrenzyType.NET_FLASH]:
                self.flash_beam_spawn_timer += 1
                if self.flash_beam_spawn_timer >= self.flash_beam_spawn_delay:
                    self.spawn_frenzy_bullets()
                    self.flash_beam_spawn_timer = 0
            # 追加弾幕タイマー（netFlashではスキップ）
            if self.frenzy_mode and self.current_frenzy_type == FrenzyType.FLASH:
                self.flash_additional_shape_timer += 1
                if self.flash_additional_shape_timer >= self.flash_additional_shape_interval:
                    for _ in range(self.difficulty):
                        shape_type = random.choice(list(ShapeType))
                        color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, CYAN])
                        x = random.randint(50, SCREEN_WIDTH - 50)
                        speed = random.uniform(2, 6)
                        shape = Shape(x, -50, shape_type, color, speed)
                        self.shapes.append(shape)
                    self.flash_additional_shape_timer = 0
        
        # 通常図形の生成
        self.shape_spawn_timer += 1
        if self.shape_spawn_timer >= self.shape_spawn_delay:
            if self.frenzy_mode and self.current_frenzy_type == FrenzyType.ALTER:
                # ALTER発狂中は下から上に向かうShapeを2個生成
                for _ in range(2):
                    shape_type = random.choice(list(ShapeType))
                    color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, CYAN])
                    x = random.randint(50, SCREEN_WIDTH - 50)
                    speed = random.uniform(2, 6)
                    shape = Shape(x, SCREEN_HEIGHT + 50, shape_type, color, -speed)
                    self.shapes.append(shape)
            elif self.frenzy_mode and self.current_frenzy_type == FrenzyType.DOUBLE:
                # DOUBLE発狂中は2サイクルに1回だけ上から1個・下から1個生成（通常弾幕の半分ずつ）
                if (self.shape_spawn_timer // self.shape_spawn_delay) % 2 == 0:
                    # 上から下
                    shape_type = random.choice(list(ShapeType))
                    color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, CYAN])
                    x = random.randint(50, SCREEN_WIDTH - 50)
                    speed = random.uniform(2, 6)
                    shape = Shape(x, -50, shape_type, color, speed)
                    self.shapes.append(shape)
                    # 下から上
                    shape_type = random.choice(list(ShapeType))
                    color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, CYAN])
                    x = random.randint(50, SCREEN_WIDTH - 50)
                    speed = random.uniform(2, 6)
                    shape = Shape(x, SCREEN_HEIGHT + 50, shape_type, color, -speed)
                    self.shapes.append(shape)
            elif not self.frenzy_mode:
                self.spawn_shape()
                self.shape_spawn_timer = 0
            
        # 図形の更新
        for shape in self.shapes[:]:
            shape.update()
            if shape.is_off_screen():
                self.shapes.remove(shape)
                
        # 発狂弾幕の更新
        for bullet in self.frenzy_bullets[:]:
            bullet.update()
            if bullet.is_off_screen():
                self.frenzy_bullets.remove(bullet)
                
        # FLASHビームの更新
        for beam in self.frenzy_flash_beams[:]:
            prev_state = beam.state
            beam.update()
            if not beam.is_active():
                self.frenzy_flash_beams.remove(beam)
                
        # プレイヤーの更新
        keys = pygame.key.get_pressed()
        self.player.update(keys)
        
        # 衝突判定
        self.check_collisions()
        
        # RUSH発狂の管理
        if self.frenzy_mode and self.current_frenzy_type == FrenzyType.RUSH:
            self.rush_mode_timer += 1
            if self.rush_mode_active:
                # 発狂中
                if self.rush_mode_timer % 4 == 0:  # 15分の1秒ごとに弾幕生成
                    self.spawn_frenzy_bullets()
                if self.rush_mode_timer >= self.rush_mode_duration:
                    self.rush_mode_active = False
                    self.rush_mode_timer = 0
            else:
                # 休憩中は弾幕を発射しない
                if self.rush_mode_timer >= self.rush_mode_rest:
                    self.rush_mode_active = True
                    self.rush_mode_timer = 0
        
        # スコア1000ごとに残機を1増やす
        if self.score >= self.next_extra_life_score:
            self.lives += 1
            self.next_extra_life_score += self.extra_life_score
        
        # ミニボーダー弾（Hard以上）
        # （この仕様は削除。MINI_BORDER発狂時のみミニボーダー弾幕が出る）
        
        # スコア自動加算（score_per_shapeが1秒ごとに加算される仕様）
        self.score_per_shape_timer += 1
        if self.score_per_shape_timer >= 60:
            self.score += self.score_per_shape
            self.score_per_shape_timer = 0
        
        # gravity用
        self.gravity_phase = 1
        self.gravity_phase_timer = 0
        self.gravity_beam_timer = 0
        self.gravity_beam_side = 0  # 0:左, 1:右
        self.gravity_side_swap_timer = 0
        self.gravity_left_is_alter = True  # True:左ALTER/右通常, False:左通常/右ALTER
        
        # ラスボス突入演出
        if self.requiem_warning:
            # WARNING演出をスキップし、即ラスボス開始
            self.requiem_warning = False
            self.requiem_started = True
            self.boss_frenzy_mode = True
            self.boss_pattern = "requiem"
            self.boss_frenzy_timer = 0
        if self.requiem_started:
            print("in requiem_started block")
            self.boss_frenzy_mode = True
            self.boss_pattern = "requiem"
            # 10形態・100秒間
            self.boss_frenzy_timer += 1
            self.requiem_phase_timer += 1
            self.requiem_total_timer += 1
            print(f"requiem_total_timer incremented: {self.requiem_total_timer}")
            print(f"boss_frenzy_timer: {self.boss_frenzy_timer}")
            print(f"requiem_phase: {self.requiem_phase}")
            # 10秒ごとに形態変化
            if self.requiem_phase_timer >= 600:
                self.requiem_phase += 1
                self.requiem_phase_timer = 0
            # 100秒経過で終了
            if self.requiem_total_timer >= 6000:
                self.requiem_started = False
                self.boss_frenzy_mode = False
                self.boss_pattern = None
                self.requiem_phase = 1
                self.requiem_phase_timer = 0
                self.requiem_total_timer = 0
                return
            # 各形態ごとに異なる弾幕
            if self.requiem_phase == 1:
                # 第一形態：rush（全方位ラッシュ、1.5倍間隔、休憩なし）
                rush_interval = int(15 * 1.5)  # 通常15フレームの1.5倍
                if self.boss_frenzy_timer % rush_interval == 0:
                    positions = [
                        (SCREEN_WIDTH // 2, 0),
                        (0, 0),
                        (SCREEN_WIDTH, 0)
                    ]
                    for pos in positions:
                        angle = random.uniform(math.pi/4, 3*math.pi/4)
                        bullet = FrenzyBullet(pos[0], pos[1], bullet_type=FrenzyType.CIRCLE_BURST)
                        bullet.angle = angle
                        bullet.speed = 10
                        bullet.size = 6
                        self.frenzy_bullets.append(bullet)
            elif self.requiem_phase == 2:
                # 第二形態：ALTER（ビーム系のみ2倍速）
                # ALTER本体（下から上に向かうShape）
                if self.boss_frenzy_timer % 8 == 0:
                    shape_type = random.choice(list(ShapeType))
                    color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, CYAN])
                    x = random.randint(50, SCREEN_WIDTH - 50)
                    speed = random.uniform(2, 6)
                    shape = Shape(x, SCREEN_HEIGHT + 50, shape_type, color, -speed)
                    self.shapes.append(shape)
                # FLASH/NET_FLASHビーム（2倍速）
                if self.boss_frenzy_timer % 30 == 0:
                    for _ in range(2):
                        edge = random.choice(['top', 'bottom', 'left', 'right'])
                        if edge == 'top':
                            x0 = random.randint(0, SCREEN_WIDTH)
                            y0 = -10
                        elif edge == 'bottom':
                            x0 = random.randint(0, SCREEN_WIDTH)
                            y0 = SCREEN_HEIGHT
                        elif edge == 'left':
                            x0 = 0
                            y0 = random.randint(0, SCREEN_HEIGHT)
                        else:
                            x0 = SCREEN_WIDTH
                            y0 = random.randint(0, SCREEN_HEIGHT)
                        tx = random.randint(0, SCREEN_WIDTH)
                        ty = random.randint(0, SCREEN_HEIGHT)
                        beam = FlashBeam((x0, y0), (tx, ty), 8, 20, 5, (255, 255, 100), (255, 220, 0))
                        self.frenzy_flash_beams.append(beam)
            elif self.requiem_phase == 3:
                # 第三形態：ボーダー第二形態＋四角ホーミング
                # ボーダー第二形態（phase2）
                border_interval = 12
                n = 15  # phase2の弾数
                angle_step = 24
                if (self.boss_frenzy_timer % border_interval) == 0:
                    center_x = SCREEN_WIDTH // 2
                    center_y = 0
                    idx = (self.boss_frenzy_timer // border_interval) % n
                    angle = math.radians(idx * angle_step + ((self.boss_frenzy_timer // border_interval) * (angle_step // 2)))
                    for da in [-12, 0, 12]:
                        a = angle + math.radians(da)
                        shape = Shape(center_x, center_y, ShapeType.CIRCLE, CYAN, 6)
                        shape.size = 8
                        shape.vx = float(math.cos(a) * 6)
                        shape.vy = float(math.sin(a) * 6)
                        self.shapes.append(shape)
                # 四角ホーミング
                if self.boss_frenzy_timer % 60 == 0:
                    bullet = FrenzyBullet(
                        random.choice([0, SCREEN_WIDTH]),
                        random.randint(0, SCREEN_HEIGHT // 2),
                        self.player.x, self.player.y,
                        FrenzyType.HOMING_SQUARE
                    )
                    self.frenzy_bullets.append(bullet)
            elif self.requiem_phase == 4:
                # 第四形態：NETFlash＋サークルバースト同時
                # NETFlash
                if self.boss_frenzy_timer % 60 == 0:
                    for _ in range(2):
                        edge = random.choice(['top', 'bottom', 'left', 'right'])
                        if edge == 'top':
                            x0 = random.randint(0, SCREEN_WIDTH)
                            y0 = -10
                        elif edge == 'bottom':
                            x0 = random.randint(0, SCREEN_WIDTH)
                            y0 = SCREEN_HEIGHT
                        elif edge == 'left':
                            x0 = 0
                            y0 = random.randint(0, SCREEN_HEIGHT)
                        else:
                            x0 = SCREEN_WIDTH
                            y0 = random.randint(0, SCREEN_HEIGHT)
                        tx = random.randint(0, SCREEN_WIDTH)
                        ty = random.randint(0, SCREEN_HEIGHT)
                        beam = FlashBeam((x0, y0), (tx, ty), 8, 40, 10, (100, 255, 255), (0, 220, 255))
                        self.frenzy_flash_beams.append(beam)
                # サークルバースト
                if self.boss_frenzy_timer % 20 == 0:
                    center_x = SCREEN_WIDTH // 2
                    center_y = SCREEN_HEIGHT // 2
                    for i in range(24):
                        angle = 2 * math.pi * i / 24
                        bullet = FrenzyBullet(center_x, center_y, bullet_type=FrenzyType.CIRCLE_BURST)
                        bullet.angle = angle
                        bullet.speed = 7
                        bullet.size = 8
                        self.frenzy_bullets.append(bullet)
        
    def check_collisions(self):
        """プレイヤーと弾幕の衝突判定"""
        player_rect = self.player.get_rect()
        
        # 通常図形との衝突
        for shape in self.shapes[:]:
            distance = math.sqrt((self.player.x - shape.x)**2 + (self.player.y - shape.y)**2)
            if distance < (self.player.width // 2 + shape.size):
                self.shapes.remove(shape)
                self.lives -= 1
                
        # 発狂弾幕との衝突
        for bullet in self.frenzy_bullets[:]:
            distance = math.sqrt((self.player.x - bullet.x)**2 + (self.player.y - bullet.y)**2)
            if distance < (self.player.width // 2 + bullet.size):
                self.frenzy_bullets.remove(bullet)
                self.lives -= 1
                
        # FLASHビームとの衝突
        for beam in self.frenzy_flash_beams[:]:
            if beam.is_colliding(player_rect):
                self.frenzy_flash_beams.remove(beam)
                self.lives -= 1
                
    def draw(self):
        """ゲーム画面を描画"""
        screen.fill(BLACK)
        
        # 発狂中の背景色変更
        if self.frenzy_mode:
            screen.fill((50, 0, 0))  # 暗い赤色
        
        # 図形を描画
        for shape in self.shapes:
            shape.draw(screen)
            
        # 発狂弾幕を描画
        for bullet in self.frenzy_bullets:
            bullet.draw(screen)
            
        # FLASHビームの描画
        for beam in self.frenzy_flash_beams:
            beam.draw(screen)
            
        # プレイヤーを描画
        self.player.draw(screen)
        
        # UIを描画
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        # 難易度ラベル表示
        diff_label = self.difficulty_labels[self.difficulty - 1] if 1 <= self.difficulty <= 5 else str(self.difficulty)
        diff_text = self.font.render(f"Difficulty: {diff_label}", True, WHITE)
        score_per_shape_text = self.font.render(f"Score/Shape: {self.score_per_shape}", True, WHITE)
        
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (10, 50))
        screen.blit(diff_text, (10, 90))
        screen.blit(score_per_shape_text, (10, 130))
        
        # 発狂情報を表示
        if self.frenzy_mode and self.current_frenzy_type is not None:
            frenzy_text = self.font.render(f"FRENZY: {self.current_frenzy_type.name}", True, RED)
            frenzy_timer_text = self.font.render(f"Time: {(self.frenzy_duration - self.frenzy_timer) // 60:.1f}s", True, RED)
            screen.blit(frenzy_text, (SCREEN_WIDTH - 300, 10))
            screen.blit(frenzy_timer_text, (SCREEN_WIDTH - 300, 50))
        # 発狂中でなければ何も表示しない
        
        # Next Frenzyタイマーの表示
        if not self.frenzy_mode and not self.boss_frenzy_mode:
            next_frenzy_text = self.font.render(f"Next Frenzy: {(self.frenzy_interval - self.frenzy_interval_timer) // 60:.1f}s", True, WHITE)
            screen.blit(next_frenzy_text, (SCREEN_WIDTH - 300, 10))
        
        # ボス弾幕までのカウントを表示
        boss_count_text = self.font.render(f"Boss Danmaku in: {self.boss_frenzy_trigger - self.frenzy_count}", True, (255, 200, 0))
        screen.blit(boss_count_text, (SCREEN_WIDTH - 300, 90))
        
        # --- ボス弾幕中の残り時間表示
        if self.boss_frenzy_mode and self.boss_pattern != "requiem":
            boss_time_left = max(0, (self.boss_frenzy_duration - self.boss_frenzy_timer) // 60)
            boss_text = self.font.render(f"Boss Danmaku Time: {boss_time_left}s", True, (255, 100, 100))
            screen.blit(boss_text, (SCREEN_WIDTH // 2 - boss_text.get_width() // 2, 10))
            # storm形態表示
            if self.boss_pattern == "storm":
                phase_text = self.font.render(f"Storm Phase: {self.storm_phase}/3", True, (100, 200, 255))
                screen.blit(phase_text, (SCREEN_WIDTH // 2 - phase_text.get_width() // 2, 50))
            # smork形態表示
            elif self.boss_pattern == "smork":
                phase_text = self.font.render(f"Smork Phase: {self.smork_phase}/3", True, (200, 200, 200))
                screen.blit(phase_text, (SCREEN_WIDTH // 2 - phase_text.get_width() // 2, 50))
            # border形態表示
            elif self.boss_pattern == "border":
                self.border_phase_timer += 1
                if self.border_phase_timer >= self.border_phase_duration:
                    self.border_phase += 1
                    self.border_phase_timer = 0
                    # 各phaseでdurationを正しくセット
                    if self.border_phase == 6 and self.difficulty >= 4:
                        self.border_phase_duration = 720
                    else:
                        self.border_phase_duration = 360
                    if self.border_phase > 6:
                        self.border_phase = 6  # 最終段階で固定
                # phaseごとの発射タイミングオフセット
                phase_offsets = {1: 0, 2: 2, 3: 4, 4: 6, 5: 8, 6: 0}
                phase_bullets = {1: 12, 2: 15, 3: 20, 4: 10, 5: 24, 6: 12}
                phase_angles = {1: 30, 2: 24, 3: 18, 4: 36, 5: 15, 6: 30}
                # 難易度ごとのway数・速度分岐
                def border_way_speed(p, base_speed):
                    if self.difficulty <= 2:  # easy/normal
                        return 1, base_speed
                    elif self.difficulty == 3:  # hard
                        if p == 2 or p == 5:
                            return 3, base_speed
                        elif p == 1 or p == 4 or p == 6:
                            return 3, base_speed
                        else:
                            return 1, base_speed
                    elif self.difficulty == 4:  # lunatic
                        if p == 2:
                            return 5, base_speed
                        elif p == 1 or p == 4 or p == 6:
                            return 3, base_speed
                        else:
                            return 1, base_speed
                    else:  # unfair
                        speed_up = 1.2 if p in [1,2,5] else 0
                        if p == 5:
                            return 3, base_speed + speed_up
                        elif p == 2:
                            return 3, base_speed + speed_up
                        elif p == 1:
                            return 3, base_speed + speed_up
                        elif p == 4 or p == 6:
                            return 3, base_speed
                        else:
                            return 1, base_speed
                # phase1の弾幕は常に発射
                phase_list = [1] + [i for i in range(max(2, self.border_phase if self.difficulty < 4 else 2), min(self.border_phase, 6)+1)]
                for p in phase_list:
                    offset = phase_offsets[p]
                    # interval分岐: unfairかつphase5のみ6フレーム、それ以外は従来通り
                    if self.difficulty == 5 and p == 5:
                        interval = 6
                    elif self.difficulty == 5 and p == 2:
                        interval = 6
                    else:
                        interval = 6 if p == 6 else 12
                    if (self.border_phase_timer - offset) % interval == 0:
                        center_x = SCREEN_WIDTH // 2
                        center_y = 0
                        n = phase_bullets[p]
                        angle_step = phase_angles[p]
                        # way数・速度決定
                        if p == 1:
                            way, spd = border_way_speed(1, 5)
                            idx = ((self.border_phase_timer - offset) // interval) % n
                            angle = math.radians(idx * angle_step + ((self.border_phase_timer // interval) * (angle_step // 2)))
                            for da in [0] if way == 1 else [-15, 0, 15]:
                                a = angle + math.radians(da)
                                shape = Shape(center_x, center_y, ShapeType.TRIANGLE, YELLOW, spd)
                                shape.size = 24
                                shape.vx = float(math.cos(a) * spd)
                                shape.vy = float(math.sin(a) * spd)
                                self.shapes.append(shape)
                        elif p == 2:
                            way, spd = border_way_speed(2, 6)
                            idx = ((self.border_phase_timer - offset) // interval) % n
                            angle = math.radians(idx * angle_step + ((self.border_phase_timer // interval) * (angle_step // 2)))
                            if self.difficulty == 5 and way == 3 and p == 2:
                                # unfair専用7way
                                for da in [-36, -24, -12, 0, 12, 24, 36]:
                                    a = angle + math.radians(da)
                                    shape = Shape(center_x, center_y, ShapeType.CIRCLE, CYAN, spd)
                                    shape.size = 8
                                    shape.vx = float(math.cos(a) * spd)
                                    shape.vy = float(math.sin(a) * spd)
                                    self.shapes.append(shape)
                            elif way == 1:
                                a = angle
                                shape = Shape(center_x, center_y, ShapeType.CIRCLE, CYAN, spd)
                                shape.size = 8
                                shape.vx = float(math.cos(a) * spd)
                                shape.vy = float(math.sin(a) * spd)
                                self.shapes.append(shape)
                            else:
                                for da in [-12, 0, 12] if way == 3 else [-24, -12, 0, 12, 24]:
                                    a = angle + math.radians(da)
                                    shape = Shape(center_x, center_y, ShapeType.CIRCLE, CYAN, spd)
                                    shape.size = 8
                                    shape.vx = float(math.cos(a) * spd)
                                    shape.vy = float(math.sin(a) * spd)
                                    self.shapes.append(shape)
                        elif p == 3:
                            way, spd = border_way_speed(3, 4)
                            idx = ((self.border_phase_timer - offset) // interval) % n
                            angle = math.radians(idx * angle_step + ((self.border_phase_timer // interval) * (angle_step // 2)))
                            shape = Shape(center_x, center_y, ShapeType.CIRCLE, BLUE, 96)
                            shape.size = 96
                            shape.vx = math.cos(angle) * spd
                            shape.vy = math.sin(angle) * spd
                            shape._shrink = True
                            shape._shrink_rate = 1/3
                            self.shapes.append(shape)
                        elif p == 4:
                            way, spd = border_way_speed(4, 5)
                            idx = ((self.border_phase_timer - offset) // interval) % n
                            angle = math.radians(idx * angle_step + ((self.border_phase_timer // interval) * (angle_step // 2)))
                            for da in [0] if way == 1 else [-10, 0, 10]:
                                a = angle + math.radians(da)
                                shape = Shape(center_x, center_y, ShapeType.CIRCLE, PURPLE, spd)
                                shape.size = 16
                                shape.vx = math.cos(a) * spd
                                shape.vy = math.sin(a) * spd
                                self.shapes.append(shape)
                        elif p == 5:
                            way, spd = border_way_speed(5, 5)
                            idx = ((self.border_phase_timer - offset) // interval) % n
                            angle = math.radians(idx * angle_step + ((self.border_phase_timer // interval) * (angle_step // 2)))
                            for da in [0] if way == 1 else [-15, 0, 15]:
                                a = angle + math.radians(da)
                                shape = Shape(center_x, center_y, ShapeType.CIRCLE, GREEN, spd)
                                shape.size = 20
                                shape.vx = math.cos(a) * spd
                                shape.vy = math.sin(a) * spd
                                self.shapes.append(shape)
                        elif p == 6:
                            way, spd = border_way_speed(6, 7)
                            shot_count = ((self.border_phase_timer - offset) // interval)
                            base_angle = math.radians(270 - shot_count * 15)
                            for da in [0] if way == 1 else [-15, 0, 15]:
                                a = base_angle + math.radians(da)
                                shape = Shape(center_x, center_y, ShapeType.CIRCLE, WHITE, spd)
                                shape.size = 18
                                shape.vx = math.cos(a) * spd
                                shape.vy = math.sin(a) * spd
                                self.shapes.append(shape)
                if self.border_phase == 6:
                    # phase6の持続時間をLunatic以上で倍に
                    if self.difficulty >= 4:
                        self.border_phase_duration = 720  # 通常の2倍
                    else:
                        self.border_phase_duration = 360
        
        # 左側にボスカウント
        boss_left_text = self.font.render(f"Boss Left: {self.requiem_boss_left}", True, (255, 100, 100))
        screen.blit(boss_left_text, (10, 170))
        # ラスボスWARNING演出
        if self.requiem_warning:
            warning_font = pygame.font.Font(None, 120)
            warning_text = warning_font.render("WARNING", True, (255, 0, 0))
            screen.blit(warning_text, (SCREEN_WIDTH // 2 - warning_text.get_width() // 2, SCREEN_HEIGHT // 2 - warning_text.get_height() // 2))
        
        # レクイエムPhaseと残り時間表示
        if self.requiem_started:
            phase_text = self.font.render(f"Requiem Phase: {self.requiem_phase}/10", True, (255, 0, 255))
            time_left = max(0, (6000 - self.requiem_total_timer) // 60)
            time_text = self.font.render(f"Requiem Time Left: {time_left}s", True, (255, 0, 255))
            screen.blit(phase_text, (SCREEN_WIDTH // 2 - phase_text.get_width() // 2, 40))
            screen.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, 80))
        
        # デバッグ表示（ラスボスタイマー監視用）
        debug_text = self.font.render(f"DEBUG: requiem_started={self.requiem_started} total_timer={self.requiem_total_timer}", True, (255,255,0))
        screen.blit(debug_text, (10, 200))
        
        pygame.display.flip()
        
    def run(self):
        """メインゲームループ"""
        running = True
        
        while running and self.lives > 0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_9:
                        # 9キーで即座に発狂開始
                        if not self.frenzy_mode:
                            self.start_frenzy()
                    elif event.key == pygame.K_8:
                        # 8キーで即座にボス弾幕開始
                        if not self.boss_frenzy_mode:
                            self.start_boss_frenzy()
                    elif event.key == pygame.K_1:
                        # 難易度アップ（最大5まで）
                        if self.difficulty < 5:
                            self.difficulty += 1
                            self.shape_spawn_delay = self.spawn_delays[self.difficulty - 1]
                            self.score_per_shape = min(self.max_score_per_shape, self.score_per_shape + 5)
                    elif event.key == pygame.K_2:
                        # 難易度ダウン（最小1まで）
                        if self.difficulty > 1:
                            self.difficulty -= 1
                            self.shape_spawn_delay = self.spawn_delays[self.difficulty - 1]
                        self.score_per_shape = max(self.min_score_per_shape, self.score_per_shape - 5)
                    elif event.key == pygame.K_p:
                        # Pキーでライフに999を追加
                        self.lives += 999
                    elif event.key == pygame.K_6:
                        # 6キーでペタフレア発狂を即座に開始
                        if not self.frenzy_mode:
                            self.frenzy_mode = True
                            self.frenzy_timer = 0
                            self.current_frenzy_type = FrenzyType.PETAFLARE
                            print("発狂開始！パターン: PETAFLARE")
                    elif event.key == pygame.K_7:
                        # 7キーでrevenge発狂を即座に開始
                        if not self.frenzy_mode:
                            self.frenzy_mode = True
                            self.frenzy_timer = 0
                            self.current_frenzy_type = FrenzyType.REVENGE
                            if hasattr(self, 'revenge_shape_timer'):
                                self.revenge_shape_timer = 0
                            print("発狂開始！パターン: REVENGE")
                    elif event.key == pygame.K_a:
                        # AキーでALTER発狂を即座に開始
                        if not self.frenzy_mode:
                            self.frenzy_mode = True
                            self.frenzy_timer = 0
                            self.current_frenzy_type = FrenzyType.ALTER
                            self.shape_spawn_delay = self.spawn_delays[self.difficulty - 1] * 2
                            print("発狂開始！パターン: ALTER")
                    elif event.key == pygame.K_d:
                        # DキーでDOUBLE発狂を即座に開始
                        if not self.frenzy_mode:
                            self.frenzy_mode = True
                            self.frenzy_timer = 0
                            self.current_frenzy_type = FrenzyType.DOUBLE
                            self.shape_spawn_delay = self.spawn_delays[self.difficulty - 1] * 2
                            print("発狂開始！パターン: DOUBLE")
                    elif event.key == pygame.K_m:
                        # mキーで即座にレクイエム（ラスボス）弾幕を開始
                        if not self.requiem_started and not self.requiem_warning:
                            self.requiem_warning = True
                            self.requiem_warning_timer = 0
                            self.shapes.clear()
                            self.frenzy_bullets.clear()
                            self.frenzy_flash_beams.clear()
                        
            self.update()
            self.draw()
            self.clock.tick(60)
            
        # ゲームオーバー画面
        if self.lives <= 0:
            self.show_game_over()
            
    def show_game_over(self):
        """ゲームオーバー画面を表示"""
        screen.fill(BLACK)
        
        game_over_text = self.font.render("Game Over", True, RED)
        final_score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
        restart_text = self.font.render("Press R to Restart, ESC to Quit", True, WHITE)
        
        screen.blit(game_over_text, 
                   (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                    SCREEN_HEIGHT // 2 - 60))
        screen.blit(final_score_text, 
                   (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, 
                    SCREEN_HEIGHT // 2))
        screen.blit(restart_text, 
                   (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                    SCREEN_HEIGHT // 2 + 60))
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # ゲームをリスタート
                        self.__init__()
                        self.run()
                        waiting = False
                    elif event.key == pygame.K_ESCAPE:
                        waiting = False

# Flashビーム用クラス
class FlashBeam:
    def __init__(self, start, target, width, warning_time, active_time, color_warning, color_active):
        self.x0, self.y0 = start  # 始点（画面端）
        self.tx, self.ty = target  # 標的点（画面内）
        self.width = width
        self.warning_time = warning_time
        self.active_time = active_time
        self.timer = 0
        self.state = 'warning'
        self.color_warning = color_warning
        self.color_active = color_active
        self.active = True
        # 直線の方向ベクトル
        dx = self.tx - self.x0
        dy = self.ty - self.y0
        angle = math.atan2(dy, dx)
        # 画面端まで延長（十分大きな長さ）
        L = max(SCREEN_WIDTH, SCREEN_HEIGHT) * 2
        self.x1 = self.x0 + math.cos(angle) * L
        self.y1 = self.y0 + math.sin(angle) * L
    def update(self):
        self.timer += 1
        if self.state == 'warning' and self.timer >= self.warning_time:
            self.state = 'active'
            self.timer = 0
        elif self.state == 'active' and self.timer >= self.active_time:
            self.active = False
    def draw(self, surface):
        color = self.color_warning if self.state == 'warning' else self.color_active
        alpha = 80 if self.state == 'warning' else 200
        beam_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(beam_surface, (*color, alpha), (self.x0, self.y0), (self.x1, self.y1), self.width)
        surface.blit(beam_surface, (0, 0))
    def is_active(self):
        return self.active
    def is_colliding(self, player_rect):
        if self.state != 'active':
            return False
        px = player_rect.centerx
        py = player_rect.centery
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        dx = x1 - x0
        dy = y1 - y0
        if dx == dy == 0:
            dist = math.hypot(px - x0, py - y0)
        else:
            t = max(0, min(1, ((px - x0) * dx + (py - y0) * dy) / (dx * dx + dy * dy)))
            proj_x = x0 + t * dx
            proj_y = y0 + t * dy
            dist = math.hypot(px - proj_x, py - proj_y)
        return dist < self.width / 2

if __name__ == "__main__":
    game = Game()
    game.run()
    pygame.quit() 