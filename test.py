import math
import random
import sys
import time
from typing import Any

import pygame as pg


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ

gameFlag = False


def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，こうかとん，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

class Character(pg.sprite.Sprite):
    def __init__(self,HP):
        super().__init__()
        self.HP = HP


class Bird(Character):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_w: (0, -1),
        pg.K_s: (0, +1),
        pg.K_a: (-1, 0),
        pg.K_d: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int], HP:int):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル 
        """
        super().__init__(HP)

        img0 = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"
        self.hyper_life = -1


        self.HpImage = pg.Surface((WIDTH, 30))
        self.HpRect = pg.draw.rect(self.HpImage, (0,255,0), pg.Rect(0,0,WIDTH,30))


    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def change_state(self, state: str, hyper_life: int):
        """
        スコア数、押下キーに応じてキャラクターの状態を強化させる
        引数１ state:キャラクターの状態("normal" or "hyper")
        引数２ hyper_life:発動時間
        """
        self.state = state
        self.hyper_life = hyper_life


    def update(self, key_lst: list[bool], screen: pg.Surface, dtime):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        # print(self.HP)
        self.HpImage = pg.Surface(((self.HP/100)*WIDTH, 30))
        self.HpRect = pg.draw.rect(self.HpImage, (0,255,0), pg.Rect(0,0,WIDTH,30))
        # pg.draw.rect(self.HpImage, (0,255,0), (0,0,100,10), width=10)
        # pg.draw.rect(self.HpImage, (0,255,0), (self.rect.centerx, self.rect.centery,500,500), width=0)

        if key_lst[pg.K_LSHIFT]:  # 左のShiftを押すと
            self.speed = 20  # 高速化する
            
        else:
            self.speed = 500 * dtime
        

        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
                
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed*mv[0], -self.speed*mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image)
            self.hyper_life -= 1
        if self.hyper_life < 0:
            self.change_state("normal", -1)
        screen.blit(self.image, self.rect)
    
    def get_direction(self) -> tuple[int, int]:
        return self.dire

class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, rad = 0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        # print(f"rad = {rad}")
        super().__init__()
        self.vx, self.vy = bird.get_direction()
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/beam.png"), angle + rad, 2.0)
        self.vx = math.cos(math.radians(angle + rad))
        self.vy = -math.sin(math.radians(angle + rad))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery + bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx + bird.rect.width*self.vx
        self.speed = 20


    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class NeoBeam(pg.sprite.Sprite):
    def __init__(self, bird: Bird, num: int):   # NeoBeamクラスのイニシャライザの引数を，こうかとんbirdとビーム数numとする
        super().__init__()
        self.num = num
        self.bird = bird

    def gen_beams(self):
        """
        NeoBeamクラスのgen_beamsメソッドで，
        ‐50°～+51°の角度の範囲で指定ビーム数の分だけBeamオブジェクトを生成し，
        リストにappendする → リストを返す
        """
        start_angle = -50
        end_angle = 51
        
        range_size = end_angle - start_angle
        angle_interval = range_size / (self.num-1)

        angles = [start_angle + i * angle_interval for i in range(self.num)]

        neo_beams = [Beam(self.bird,rad=angles[i]) for i in range(self.num)]
        return neo_beams
    


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load("ex05/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(Character):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"ex05/fig/alien{i}.png") for i in range(1, 4)]

    imgs[0] = pg.transform.scale(imgs[0],(random.randint(90,150),random.randint(90,150)))
    imgs[1] = pg.transform.scale(imgs[1],(random.randint(90,150),random.randint(90,150)))
    imgs[2] = pg.transform.scale(imgs[2],(random.randint(90,150),random.randint(90,150)))
    
    
    def __init__(self,HP):
        super().__init__(HP)

        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        # cx = random.randint(WIDTH-50,WIDTH+50)
        # cy = random.randint(HEIGHT-50, HEIGHT+50)
        
        while(True):
            cx = random.randint(0-50,WIDTH+50)
            cy = random.randint(HEIGHT, HEIGHT+50)
            
            if ((cy < 0) or (cy > HEIGHT)):
                break
        

        self.rect.centerx = cx
        self.rect.centery = cy

        self.HpImage = pg.Surface((200, 10))
        self.HpRect = pg.draw.rect(self.HpImage, (0,255,0), pg.Rect(self.rect.bottomleft[0],self.rect.bottomleft[1],200,10))
        


    def update(self, bird:Bird, screen):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """

        self.vx, self.vy = calc_orientation(self.rect, bird.rect)

        self.rect.centerx +=  3* self.vx
        self.rect.centery +=  3* self.vy



        self.HpImage = pg.Surface(((self.HP/100)*200, 10))
        self.HpRect = pg.draw.rect(self.HpImage, (0,0,0), pg.Rect(self.rect.bottomleft[0],self.rect.bottomleft[1],200,10))
        self.HpImage.fill((255,0,0))
        screen.blit(self.HpImage, self.HpRect)

        if self.HP <= 0:
            self.kill()

class BOSS(Character):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"ex05/fig/alien{i}.png") for i in range(1, 4)]

    imgs[0] = pg.transform.scale(imgs[0],(random.randint(400,600),random.randint(400,600)))
    imgs[1] = pg.transform.scale(imgs[1],(random.randint(400,600),random.randint(400,600)))
    imgs[2] = pg.transform.scale(imgs[2],(random.randint(400,600),random.randint(400,600)))

    
    
    def __init__(self,HP):
        super().__init__(HP)

        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        # cx = random.randint(WIDTH-50,WIDTH+50)
        # cy = random.randint(HEIGHT-50, HEIGHT+50)
        
        while(True):
            cx = random.randint(0-50,WIDTH+50)
            cy = random.randint(HEIGHT, HEIGHT+30)
            
            if ((cy < 0) or (cy > HEIGHT)):
                break
        

        self.rect.centerx = cx
        self.rect.centery = cy

        self.HpImage = pg.Surface((500, 50))
        self.HpRect = pg.draw.rect(self.HpImage, (0,255,0), pg.Rect(self.rect.bottomleft[0],self.rect.bottomleft[1],500,50))


    def update(self, bird:Bird,screen):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """

        self.vx, self.vy = calc_orientation(self.rect, bird.rect)

        self.rect.centerx +=  3* self.vx
        self.rect.centery +=  3* self.vy

        self.HpImage = pg.Surface(((self.HP/100)*500, 50))
        self.HpRect = pg.draw.rect(self.HpImage, (0,0,0), pg.Rect(self.rect.bottomleft[0],self.rect.bottomleft[1],500,50))
        self.HpImage.fill((255,0,0))
        screen.blit(self.HpImage, self.HpRect)


        if self.HP <= 0:
            global gameFlag
            gameFlag = True
            self.kill()
            


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 100)
        self.color = (255, 0, 0)
        self.score = 0
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH/2, 100

    def score_up(self, add):
        self.score += add

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.image, self.rect)




def main():
    
    pg.display.set_caption("KOUKATON SUVIVER")
    
    bg_img = pg.image.load("ex05/fig/haikei.png")
    bg_img = pg.transform.scale(bg_img,(WIDTH,HEIGHT))

    screen = pg.display.set_mode((WIDTH, HEIGHT))

    score = Score()

    bird = Bird(3, (900, 400), 100)
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()


    tmr = 0
    clock = pg.time.Clock()

    dtime  = 0

    BossFlag = False
    killFlag = False

    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE and key_lst[pg.K_LSHIFT] :
                # print("f_key ON")
                """
                発動条件が満たされたら，NeoBeamクラスのイニシャライザにこうかとんと
                ビーム数を渡し，戻り値のリストをBeamグループに追加する
                """
                n_beams = NeoBeam(bird,110)
                beam_lst = n_beams.gen_beams()
                # print(f"list in {beam_lst}")
                for i in beam_lst:
                    beams.add(i)
            
            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))


        if tmr%20 == 0:
            if score.score < 30:
                beams.add(Beam(bird))
            else:
                n_beams = NeoBeam(bird,3 + score.score%10)
                beam_lst = n_beams.gen_beams()
                for i in beam_lst:
                    beams.add(i)

        if tmr > 200:
            if tmr % 400:
                if BossFlag == False:
                    emys.add(BOSS(100))
                    BossFlag = True
            
        screen.blit(bg_img, [0, 0])


        if tmr%50 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy(20))
            


        # print(pg.sprite.groupcollide(emys, beams, False, True))

        for emy in pg.sprite.groupcollide(emys, beams, False, True).keys():
            emy.HP -= 10
            
            exps.add(Explosion(emy, 10))  # 爆発エフェクト
            # print(emy.HP)
            if emy.HP <= 0:
                score.score_up(10)
            

        for b in pg.sprite.spritecollide(bird, emys, False, False):
            bird.HP -= 0.6
            # print(bird.HP)

            if bird.HP <= 0:
                font = pg.font.Font(None, 250)
                image = font.render(f"Game Over", 0, (255,0,0))
                img_rct = image.get_rect()
                img_rct.center = (WIDTH/2, HEIGHT/2)
                screen.blit(image, img_rct)

                bird.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
            
        
        if gameFlag == True:
            # game clear
            font = pg.font.Font(None, 250)
            image = font.render(f"Game Clear", 0, (0,255,0))
            img_rct = image.get_rect()
            img_rct.center = (WIDTH/2, HEIGHT/2)
            screen.blit(image, img_rct)


            bird.change_img(9, screen)
            score.update(screen)
            screen.blit(bird.HpImage, bird.HpRect)
            pg.display.update()
            time.sleep(2)
            return
            
        print(gameFlag)


        bird.update(key_lst, screen, dtime)
        

        emys.draw(screen)
        emys.update(bird,screen)
        

        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)


        score.update(screen)        
        screen.blit(bird.HpImage, bird.HpRect)

        beams.update()
        beams.draw(screen)
        
        pg.display.update()
        tmr += 1
        dtime = clock.tick(50)/1000
        # clock.tick(50)



if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()



