import x68k
import random
import time
import sys
from uctypes import addressof
from struct import pack

# バージョン
VERSION = const("2023.04.30")

# ボードクラス
class Board:

  # クラス変数: 盤面カラー
  BOARD_COLOR = const(0b01000_00011_00011_1)

  # クラス変数: 盤面横幅、縦幅
  BOARD_WIDTH  = const(400)
  BOARD_HEIGHT = const(480)

  # クラス変数: 1マスの横幅、縦幅
  GRID_WIDTH  = const(50)
  GRID_HEIGHT = const(60)

  # コンストラクタ
  def __init__(self, board_pos, bitmap_black, bitmap_white):

    # 盤面の初期配置    
    self.board = [ 0 ] * 8 * 8     # 8x8 の盤面 (0:置かれていない 1:黒 2:白 -1:黒書き換え -2:白書き換え)
    self.board[ 3 + 3 * 8 ] = -2
    self.board[ 4 + 3 * 8 ] = -1
    self.board[ 3 + 4 * 8 ] = -1
    self.board[ 4 + 4 * 8 ] = -2

    # 盤面位置
    self.board_x = board_pos[0]                       # 盤面表示開始位置X座標
    self.board_y = board_pos[1]                       # 盤面表示開始位置Y座標

    # GVRAM 参照
    self.gvram = x68k.GVRam()

    # TVRAM 参照
    self.tvram = x68k.TVRam()
    self.tvram.palet(1, Board.BOARD_COLOR)

    # 駒のビットマップ参照
    self.bitmap_black = bitmap_black
    self.bitmap_white = bitmap_white

    # 盤全体を塗りつぶす(テキスト画面)
    self.tvram.fill(0, self.board_x, self.board_y, Board.BOARD_WIDTH, Board.BOARD_HEIGHT)

    # ラインを引く(テキスト画面)
    for i in range(8):
      # 縦線
      self.tvram.yline(0, self.board_x + i * Board.GRID_WIDTH, self.board_y, Board.BOARD_HEIGHT, 0)
      # 横線
      self.tvram.xline(0, self.board_x, self.board_y + i * Board.GRID_HEIGHT, Board.BOARD_WIDTH, 0)

  # 描画
  def repaint(self, vsync=True):

    # vsync待ち
    if vsync:
      x68k.vsync()

    # 更新があったマスの駒描画(グラフィック)
    for i in range(8):
      for j in range(8):
        if self.board[ i + j * 8 ] == -1:              # 黒書き換えあり
          self.gvram.put(self.board_x + i * Board.GRID_WIDTH,
                         self.board_y + j * Board.GRID_HEIGHT,
                         self.board_x + ( i + 1 ) * Board.GRID_WIDTH  - 1,
                         self.board_y + ( j + 1 ) * Board.GRID_HEIGHT - 1,
                         self.bitmap_black)
          self.board[ i + j * 8 ] = 1
        elif self.board[ i + j * 8 ] == -2:            # 白書き換えあり
          self.gvram.put(self.board_x + i * Board.GRID_WIDTH,
                         self.board_y + j * Board.GRID_HEIGHT,
                         self.board_x + ( i + 1 ) * Board.GRID_WIDTH - 1,
                         self.board_y + ( j + 1 ) * Board.GRID_HEIGHT - 1,
                         self.bitmap_white)
          self.board[ i + j * 8 ] = 2

  # 駒を置けるかどうかのチェック
  def is_placeable(self, pos, color):
    if self.board[ pos[0] + pos[1] * 8 ] == 0:
      return True
    else:
      return False

  # 駒を置く
  def place(self, pos, color):
    self.board[ pos[0] + pos[1] * 8 ] = (-1) * color

  # 駒を数える
  def count(self):
    count_b = self.board.count(1) + self.board.count(-1)
    count_w = self.board.count(2) + self.board.count(-2)
    return (count_b, count_w)      

# カーソルクラス
class Cursor:

  # クラス変数 - パターン定義
  CURSOR_PATTERN = bytes([0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11,
                          0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                          0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 ])

  # クラス変数 - パレット定義
  CURSOR_PALETTE = ( 0b11100_11100_10000_0 )

  # コンストラクタ
  def __init__(self, board_pos, cursor_pos):

    # Sprite 参照
    self.sprite = x68k.Sprite()

    # 基準位置
    self.board_x = board_pos[0] + 16 + int((Board.GRID_WIDTH - 32)/2)
    self.board_y = board_pos[1] + 16 + Board.GRID_HEIGHT - 4

    # スプライト初期化
    self.sprite.init()
    self.sprite.clr()
    self.sprite.defcg(0, Cursor.CURSOR_PATTERN, 1)
    self.sprite.palet(1, Cursor.CURSOR_PALETTE, 1)
    self.sprite.disp()

    # 初期位置
    self.pos_x = cursor_pos[0]
    self.pos_y = cursor_pos[1]

  # カーソル表示 (スプライト)
  def scroll(self, on=True, vsync=True):

    # プライオリティ ... 3:表示する 0:表示しない
    priority = 3 if on else 0

    # vsync待ち(まとめて複数表示するのでここで待つ)
    if vsync:
      x68k.vsync()

    # スクロール
    self.sprite.set(0, 
                    self.board_x + self.pos_x * Board.GRID_WIDTH, 
                    self.board_y + self.pos_y * Board.GRID_HEIGHT,
                    (1 << 8) | 0, priority, False)
    self.sprite.set(1, 
                    self.board_x + self.pos_x * Board.GRID_WIDTH + 16, 
                    self.board_y + self.pos_y * Board.GRID_HEIGHT,
                    (1 << 8) | 0, priority, False)

  # カーソル左移動
  def move_left(self):
    self.pos_x = ( self.pos_x - 1 + 8 ) % 8
    self.scroll()

  # カーソル右移動
  def move_right(self):
    self.pos_x = ( self.pos_x + 1 ) % 8
    self.scroll()

  # カーソル上移動
  def move_up(self):
    self.pos_y = ( self.pos_y - 1 + 8 ) % 8
    self.scroll()

  # カーソル下移動
  def move_down(self):
    self.pos_y = ( self.pos_y + 1 ) % 8
    self.scroll()

# 512x512x65536イメージファイルの表示
def load_image(image_file):
  with open(image_file, "rb") as f:
    gvram = x68k.GVRam()
    for y in range(0, 512, 64):
      line_data = f.read(512 * 2 * 64)
      gvram.put(0, y, 511, y + 63, line_data)

# メイン
def main():

  # randomize
  random.seed(int(time.time() * 10))

  # cursor off
  x68k.curoff()

  # function key display off
  funckey_mode = x68k.dos(x68k.d.CONCTRL,pack('hh',14,3))

  # 駒ビットマップデータのロード
  bitmap_black = None
  with open("koma_b.dat", "rb") as f:
    bitmap_black = f.read()
  bitmap_white = None
  with open("koma_w.dat", "rb") as f:
    bitmap_white = f.read()
  if bitmap_black is None or bitmap_white is None:
    print("error: data load error.")
    sys.exit(1)


  # メインループ
  abort = False
  while abort is False:

    # タイトル画面

    # 512 x 512 x 65536 (31kHz) mode
    x68k.vsync()
    x68k.crtmod(12, True)

    # スプライト＞テキスト＞グラフィックの順に画面プライオリティを変更する
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82500, d1=0b00000110_11100100)

    # タイトルビットマップ表示
    load_image("title3.dat")

    # タイトル文字表示
    print("\x1b[25;25H\x1b[37mPUSH SPACE KEY\x1b[m", end="")

    # タイトルキー待ち
    while True:
      scan_code = ( x68k.iocs(x68k.i.B_KEYINP) >> 8 ) & 0x7f
      if scan_code == 0x01:       # esc key
        abort = True
        break
      elif scan_code == 0x35:     # space key
        break

    # ESCが押された？
    if abort:
      break


    # ゲーム画面

    # 512 x 512 x 65536 (31kHz) mode
    x68k.vsync()
    x68k.crtmod(12, True)

    # スプライト＞グラフィック＞テキストの順に画面プライオリティを変更する
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82500, d1=0b00001001_11100100)

    # ボード初期化
    board = Board((0, 0), bitmap_black, bitmap_white)
    board.repaint()

    # カーソル初期化
    cursor = Cursor((0, 0), (0, 0))
    cursor.scroll()

    # インフォメーション表示
    print("\x1b[2;53H\x1b[mMicroReversi\x1b[m", end="")
    print("\x1b[3;53H\x1b[mPRO-68K     \x1b[m", end="")

    print("\x1b[6;53H\x1b[37mCOMPUTER\x1b[m", end="")
    print("\x1b[8;53H白(後手)", end="")
    print("\x1b[10;53H2枚", end="")
    
    print("\x1b[14;53H\x1b[37mPLAYER\x1b[m", end="")
    print("\x1b[16;53H黒(先手)", end="")
    print("\x1b[18;53H2枚", end="")

    print("\x1b[22;53Hカーソルキー", end="")
    print("\x1b[23;53Hの上下左右で", end="")
    print("\x1b[24;53Hマスを選択し", end="")
    print("\x1b[25;53Hリターンで駒", end="")
    print("\x1b[26;53Hを置きます", end="")
    print("\x1b[29;53HESCで退出", end="")

    # ゲームループ
    abort = False
    while abort is False:

      # キーボードでカーソルを移動させスペースキーまたはリターンキーで確定
      while True:
        if x68k.iocs(x68k.i.B_KEYSNS):
          scan_code = ( x68k.iocs(x68k.i.B_KEYINP) >> 8 ) & 0x7f
          if scan_code == 0x01:       # esc key
            abort = True
            break
          elif scan_code == 0x3b:     # left key
            cursor.move_left()
          elif scan_code == 0x3d:     # right key
            cursor.move_right()
          elif scan_code == 0x3c:     # up key
            cursor.move_up()
          elif scan_code == 0x3e:     # down key
            cursor.move_down()
          elif scan_code == 0x35:     # space key
            break
          elif scan_code == 0x1d:     # return key
            break

      # ESCキーが押された？
      if abort:
        break

      # カーソル位置に本当における？
      if board.is_placeable((cursor.pos_x, cursor.pos_y), 1):
        board.place((cursor.pos_x, cursor.pos_y), 1)
        board.repaint()
        counts = board.count()
        print(f"\x1b[10;53H{counts[1]}枚 ", end="")
        print(f"\x1b[18;53H{counts[0]}枚 ", end="")


  # 終了処理

  # flush key buffer
  x68k.dos(x68k.d.KFLUSH,pack('h',0))  

  # 768 x 512 x 16 (31kHz) mode
  x68k.crtmod(16, True)

  # cursor on
  x68k.curon()

  # resume function key display mode
  x68k.dos(x68k.d.CONCTRL,pack('hh',14,funckey_mode))

if __name__ == "__main__":
  main()
  