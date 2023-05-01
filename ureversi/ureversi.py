import x68k
import random
import time
import sys
from struct import pack

# バージョン
VERSION = const("2023.05.01")

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

  # 8方向チェック用オフセット
  DX = [  0,  1,  1,  1,  0, -1, -1, -1 ]
  DY = [ -1, -1,  0,  1,  1,  1,  0, -1 ]

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
  def get_placeable_directions(self, pos, color):

    # 置ける方向リスト
    directions = []

    # 既に何か置いてあったら全然ダメ
    if self.board[ pos[0] + pos[1] * 8 ] != 0:
      return directions   # 空リスト

    # 8方向確認
    for i in range(8):

      # チェック開始基準点
      cx = pos[0]
      cy = pos[1]

      # チェック用キューイング
      cs = []
      while True:

        # チェック対象位置
        cx += Board.DX[i]
        cy += Board.DY[i]

        # 盤外ならストップ
        if cx < 0 or cx > 7 or cy < 0 or cy > 7:
          break   

        # 未表示かもしれないので絶対値で
        c = abs(self.board[ cx + cy * 8 ])

        # 何も置いてなければストップ
        if c == 0:
          break

        # キューに追加
        cs.append(c)

      # キューを先頭から見て [ 自分以外の色が1個以上 + 自分の色 ] となっていれば置ける
      cc = False
      rc = False
      while len(cs) > 0:
        ct = cs.pop(0)
        if ct == color:           # 自分の色を見つけたら終了
          rc = cc                 # 既に自分以外の色を見つけているかで判定
          break
        else:
          cc = True               # 自分以外の色を見つけた

      # この方向に置けるのであれば、置ける方向リストに追加
      if rc:
        directions.append(i)

    return directions

  # 駒を置く
  def place(self, pos, color):

    # 置けたかどうか
    rc = False

    # 置ける方向のチェック
    directions = self.get_placeable_directions(pos, color)
    if len(directions) == 0:
      return rc

    # 置く
    self.board[ pos[0] + pos[1] * 8 ] = (-1) * color

    # ひっくり返す
    for i in directions:
      cx = pos[0]
      cy = pos[1]
      while True:
        cx += Board.DX[i]
        cy += Board.DY[i]
        if cx < 0 or cx > 7 or cy < 0 or cy > 7:
          break
        c = abs(self.board[ cx + cy * 8 ])
        if c == color:
          break
        self.board[ cx + cy * 8 ] = (-1) * color
        self.repaint()
        #time.sleep(0.05)

    # 盤面再描画
#    self.repaint()

    # 置けたよ
    rc = True

    return rc

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

# 指定サイズ・指定位置メモリ上イメージの表示
def put_image(pos, size, bitmap_image):
  gvram = x68k.GVRam()
  gvram.put(pos[0], pos[1], pos[0] + size[0] - 1, pos[1] + size[1] - 1, bitmap_image)

# 512x512x65536イメージファイルの表示
def load_full_image(image_file):
  with open(image_file, "rb") as f:
    
    # 一旦グラフィックOFF
    b = x68k.iocs(x68k.i.B_WPEEK, a1=0xe82600) & 0xffe0
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=b)

    # ファイルの内容をGVRAMに転送
    gvram = x68k.GVRam()
    for y in range(0, 512, 64):
      line_data = f.read(512 * 2 * 64)
      gvram.put(0, y, 511, y + 63, line_data)

    # グラフィックON
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=(b | 0x0f))  

# 342x512x65536イメージファイルの縦スクロール表示
def load_portrait_image(image_file):
  with open(image_file, "rb") as f:
    
    # 384x256x65536モード (IPL-ROM 1.6 or CRTMOD16.X)
    x68k.crtmod(31, True)

    # 表示領域外にも描けるようにクリッピング領域を広げる
    x68k.iocs(x68k.i.WINDOW, d1=0, d2=0, d3=511, d4=511)

    # 一旦グラフィックOFF
    b = x68k.iocs(x68k.i.B_WPEEK, a1=0xe82600) & 0xffe0
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=b)

    # ファイルの内容をGVRAMに転送
    gvram = x68k.GVRam()
    for y in range(0, 512, 64):
      line_data = f.read(342 * 2 * 64)
      gvram.put(22, y, 363, y + 63, line_data)

    # 初期スクロール位置
    x68k.iocs(x68k.i.SCROLL, d1=0, d2=0, d3=256)
    x68k.iocs(x68k.i.SCROLL, d1=1, d2=0, d3=256)
    x68k.iocs(x68k.i.SCROLL, d1=2, d2=0, d3=256)
    x68k.iocs(x68k.i.SCROLL, d1=3, d2=0, d3=256)

    # グラフィックON
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=(b | 0x0f))  

    # 一呼吸置いて
    time.sleep(2.000)

    # お楽しみ縦スクロール
    for i in range(256):
      y = 255 - i
      x68k.vsync()
      x68k.iocs(x68k.i.SCROLL, d1=0, d2=0, d3=y)
      x68k.iocs(x68k.i.SCROLL, d1=1, d2=0, d3=y)
      x68k.iocs(x68k.i.SCROLL, d1=2, d2=0, d3=y)
      x68k.iocs(x68k.i.SCROLL, d1=3, d2=0, d3=y)

# メイン
def main():

  # randomize
  random.seed(int(time.time() * 10))

  # IPL-ROM version check
  rom_version = x68k.iocs(x68k.i.ROMVER) >> 24
  if rom_version < 0x16:
    # CRTMOD16.X check
    crtmod_vector = x68k.iocs(x68k.i.B_LPEEK,a1=(0x000400 + 4 * 0x10))  # check IOCS $10 vector
    if crtmod_vector < 0 or (crtmod_vector >= 0xfe0000 and crtmod_vector <= 0xffffff):
      raise RuntimeError("CRTMOD16.X is required for IPL-ROM 1.5 or lower.")

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

  # COM顔ビットマップデータのロード
  bitmap_com1 = None
  with open("com1.dat", "rb") as f:
    bitmap_com1 = f.read()

  # メインループ
  abort = False
  while abort is False:

    # タイトル画面 -------------------------------------------------------------------------------

    # 512 x 512 x 65536 (31kHz) mode
    x68k.vsync()
    x68k.crtmod(12, True)

    # スプライト＞テキスト＞グラフィックの順に画面プライオリティを変更する
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82500, d1=0b00000110_11100100)

    # タイトルビットマップ表示
    load_full_image("title3.dat")

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


    # ゲーム画面 -------------------------------------------------------------------------------

    # 先手後手
    if random.randint(0,1) == 0:
      # COMが先手(黒)
      color_computer = 1
      color_player = 2
    else:
      # COMが後手(白)
      color_computer = 2
      color_player = 1

    # 512 x 512 x 65536 (31kHz) mode
    x68k.vsync()
    x68k.crtmod(12, True)

    # スプライト＞グラフィック＞テキストの順に画面プライオリティを変更する
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82500, d1=0b00001001_11100100)

    # 一旦グラフィック・テキスト・スプライトOFF
    b = x68k.iocs(x68k.i.B_WPEEK, a1=0xe82600) & 0xff00
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=b)

    # ボード初期化
    board = Board((0, 4), bitmap_black, bitmap_white)
    board.repaint()

    # カーソル初期化
    cursor = Cursor((0, 4), (0, 0))
    cursor.scroll()

    # インフォメーション表示
    print("\x1b[2;53H\x1b[mMicroReversi\x1b[m", end="")
    print("\x1b[3;53H\x1b[mPRO-68K     \x1b[m", end="")

    print("\x1b[6;53H\x1b[37mCOMPUTER\x1b[m", end="")
    if color_computer == 1:
      print("\x1b[16;53H黒(先手)", end="")
    else:
      print("\x1b[16;53H白(後手)", end="")
    print("\x1b[18;53H2枚", end="")
    
    print("\x1b[22;53H\x1b[37mPLAYER\x1b[m", end="")
    if color_player == 1:
      print("\x1b[24;53H黒(先手)", end="")
    else:
      print("\x1b[24;53H白(後手)", end="")      
    print("\x1b[26;53H2枚", end="")

    print("\x1b[32;1H[←↑↓→]:マス選択 [RET/SP]:駒を置く [p]:パス [ESC]:終了", end="")

    # COMビットマップ表示
    put_image((408, 104), (104, 124), bitmap_com1)

    # グラフィック・テキスト・スプライトON
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=(b | 0x6f))

    # ゲームループ
    game_end = False      # ゲーム終了フラグ
    color_active = 1      # 現在の手番の色
    pass_count = 0        # 現在までのパス回数
    while game_end is False and abort is False:

      computer_placed = False
      player_placed = False

      if color_active == color_computer:
      
        # COMの手番

        # カーソルを消す
        cursor.scroll(False)

        # 試行順 カド(0,7,56,63)は最優先
        pos = [ 0, 7, 56, 63 ] + list(range(1,7)) + list(range(8,56)) + list(range(57,63))

        # 試行順のシャッフル
        for i in range(100):
          a = random.randint(0, 3)
          b = random.randint(0, 3)
          c = random.randint(4, 63)
          d = random.randint(4, 63)
          pos[ a ], pos[ b ] = pos[ b ], pos[ a ]
          pos[ c ], pos[ d ] = pos[ d ], pos[ c ]

        for p in pos:
          # 置けるか？
          if board.place((p % 8, p // 8), color_computer):
            # 置けた
            computer_placed = True
            break

      else:
        
        # 自分の手番

        # flush key buffer
        x68k.dos(x68k.d.KFLUSH,pack('h',0))

        # カーソルを表示する
        cursor.scroll(True)

        while player_placed is False and abort is False:

          # キーボードでカーソルを移動させスペースキーまたはリターンキーで確定
          pass_button = False
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
              elif scan_code == 0x1a:     # p key
                # 本当に置くとこない？
                placeable = False
                for i in range(64):
                  if len(board.get_placeable_directions((i % 8, i // 8), color_player)) > 0:
                    placeable = True
                    break
                # 本当に置くところなかったのでパス
                if placeable is False:
                  pass_button = True
                  break

          # ESCキーが押された？
          if abort:
            break

          # パス有効
          if pass_button:
            break

          # カーソル位置に本当における？
          if board.place((cursor.pos_x, cursor.pos_y), color_player):
            # 置けた
            player_placed = True
            break

      # 置けた場合
      if computer_placed or player_placed:

        # 枚数表示更新
        counts = board.count()
        if color_computer == 1:
          print(f"\x1b[18;53H{counts[0]}枚 ", end="")
          print(f"\x1b[26;53H{counts[1]}枚 ", end="")
        else:
          print(f"\x1b[18;53H{counts[1]}枚 ", end="")
          print(f"\x1b[26;53H{counts[0]}枚 ", end="")

        # パーフェクトゲーム？
        if counts[0] == 0 or counts[1] == 0:
          game_end = True
          break          

        # もう置く場所ない？
        if counts[0] + counts[1] == 64:
          game_end = True
          break

        # パス回数リセット
        pass_count = 0

      else:

        # パスが2回続いたら終了
        pass_count += 1
        if pass_count >= 2:
          game_end = True
          break

      # 手番交代
      if color_active == 1:
        color_active = 2
      else:
        color_active = 1

    # 1ゲーム終了
    if abort is False:

      # 結果表示
      computer_win = None
      counts = board.count()
      if counts[0] > counts[1]:
        computer_win = (color_computer == 1)
        print("\x1b[32;1H黒の勝ちです\x1b[K", end="")
      elif counts[0] < counts[1]:
        computer_win = (color_computer == 2)
        print("\x1b[32;1H白の勝ちです\x1b[K", end="")
      else:
        print("\x1b[32;1H引き分けです\x1b[K", end="")      

      # 3秒待つ
      time.sleep(3.000)

      # ビジュアルシーン
      if computer_win is None:
        # 引き分けなら何もなし
        pass
      elif computer_win:
        # COMの勝ち
        load_portrait_image(f"win{random.randint(1,2)}.dat")
      else:
        # COMの負け
        load_portrait_image(f"lose{random.randint(1,2)}.dat")

      # 文字表示
      print("\x1b[2;2H\x1b[37mPUSH ANY KEY\x1b[m", end="")

      # flush key buffer
      x68k.dos(x68k.d.KFLUSH,pack('h',0))

      # キー待ち
      while True:
        scan_code = ( x68k.iocs(x68k.i.B_KEYINP) >> 8 ) & 0x7f
        if scan_code != 0:
          break

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
  