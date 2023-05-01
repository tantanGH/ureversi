import x68k
import random
import time
import sys
from struct import pack

# �o�[�W����
VERSION = const("2023.05.01")

# �{�[�h�N���X
class Board:

  # �N���X�ϐ�: �ՖʃJ���[
  BOARD_COLOR = const(0b01000_00011_00011_1)

  # �N���X�ϐ�: �Ֆʉ����A�c��
  BOARD_WIDTH  = const(400)
  BOARD_HEIGHT = const(480)

  # �N���X�ϐ�: 1�}�X�̉����A�c��
  GRID_WIDTH  = const(50)
  GRID_HEIGHT = const(60)

  # 8�����`�F�b�N�p�I�t�Z�b�g
  DX = [  0,  1,  1,  1,  0, -1, -1, -1 ]
  DY = [ -1, -1,  0,  1,  1,  1,  0, -1 ]

  # �R���X�g���N�^
  def __init__(self, board_pos, bitmap_black, bitmap_white):

    # �Ֆʂ̏����z�u    
    self.board = [ 0 ] * 8 * 8     # 8x8 �̔Ֆ� (0:�u����Ă��Ȃ� 1:�� 2:�� -1:���������� -2:����������)
    self.board[ 3 + 3 * 8 ] = -2
    self.board[ 4 + 3 * 8 ] = -1
    self.board[ 3 + 4 * 8 ] = -1
    self.board[ 4 + 4 * 8 ] = -2

    # �Ֆʈʒu
    self.board_x = board_pos[0]                       # �Ֆʕ\���J�n�ʒuX���W
    self.board_y = board_pos[1]                       # �Ֆʕ\���J�n�ʒuY���W

    # GVRAM �Q��
    self.gvram = x68k.GVRam()

    # TVRAM �Q��
    self.tvram = x68k.TVRam()
    self.tvram.palet(1, Board.BOARD_COLOR)

    # ��̃r�b�g�}�b�v�Q��
    self.bitmap_black = bitmap_black
    self.bitmap_white = bitmap_white

    # �ՑS�̂�h��Ԃ�(�e�L�X�g���)
    self.tvram.fill(0, self.board_x, self.board_y, Board.BOARD_WIDTH, Board.BOARD_HEIGHT)

    # ���C��������(�e�L�X�g���)
    for i in range(8):
      # �c��
      self.tvram.yline(0, self.board_x + i * Board.GRID_WIDTH, self.board_y, Board.BOARD_HEIGHT, 0)
      # ����
      self.tvram.xline(0, self.board_x, self.board_y + i * Board.GRID_HEIGHT, Board.BOARD_WIDTH, 0)

  # �`��
  def repaint(self, vsync=True):

    # vsync�҂�
    if vsync:
      x68k.vsync()

    # �X�V���������}�X�̋�`��(�O���t�B�b�N)
    for i in range(8):
      for j in range(8):
        if self.board[ i + j * 8 ] == -1:              # ��������������
          self.gvram.put(self.board_x + i * Board.GRID_WIDTH,
                         self.board_y + j * Board.GRID_HEIGHT,
                         self.board_x + ( i + 1 ) * Board.GRID_WIDTH  - 1,
                         self.board_y + ( j + 1 ) * Board.GRID_HEIGHT - 1,
                         self.bitmap_black)
          self.board[ i + j * 8 ] = 1
        elif self.board[ i + j * 8 ] == -2:            # ��������������
          self.gvram.put(self.board_x + i * Board.GRID_WIDTH,
                         self.board_y + j * Board.GRID_HEIGHT,
                         self.board_x + ( i + 1 ) * Board.GRID_WIDTH - 1,
                         self.board_y + ( j + 1 ) * Board.GRID_HEIGHT - 1,
                         self.bitmap_white)
          self.board[ i + j * 8 ] = 2

  # ���u���邩�ǂ����̃`�F�b�N
  def get_placeable_directions(self, pos, color):

    # �u����������X�g
    directions = []

    # ���ɉ����u���Ă�������S�R�_��
    if self.board[ pos[0] + pos[1] * 8 ] != 0:
      return directions   # �󃊃X�g

    # 8�����m�F
    for i in range(8):

      # �`�F�b�N�J�n��_
      cx = pos[0]
      cy = pos[1]

      # �`�F�b�N�p�L���[�C���O
      cs = []
      while True:

        # �`�F�b�N�Ώۈʒu
        cx += Board.DX[i]
        cy += Board.DY[i]

        # �ՊO�Ȃ�X�g�b�v
        if cx < 0 or cx > 7 or cy < 0 or cy > 7:
          break   

        # ���\����������Ȃ��̂Ő�Βl��
        c = abs(self.board[ cx + cy * 8 ])

        # �����u���ĂȂ���΃X�g�b�v
        if c == 0:
          break

        # �L���[�ɒǉ�
        cs.append(c)

      # �L���[��擪���猩�� [ �����ȊO�̐F��1�ȏ� + �����̐F ] �ƂȂ��Ă���Βu����
      cc = False
      rc = False
      while len(cs) > 0:
        ct = cs.pop(0)
        if ct == color:           # �����̐F����������I��
          rc = cc                 # ���Ɏ����ȊO�̐F�������Ă��邩�Ŕ���
          break
        else:
          cc = True               # �����ȊO�̐F��������

      # ���̕����ɒu����̂ł���΁A�u����������X�g�ɒǉ�
      if rc:
        directions.append(i)

    return directions

  # ���u��
  def place(self, pos, color):

    # �u�������ǂ���
    rc = False

    # �u��������̃`�F�b�N
    directions = self.get_placeable_directions(pos, color)
    if len(directions) == 0:
      return rc

    # �u��
    self.board[ pos[0] + pos[1] * 8 ] = (-1) * color

    # �Ђ�����Ԃ�
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

    # �Ֆʍĕ`��
#    self.repaint()

    # �u������
    rc = True

    return rc

  # ��𐔂���
  def count(self):
    count_b = self.board.count(1) + self.board.count(-1)
    count_w = self.board.count(2) + self.board.count(-2)
    return (count_b, count_w)      

# �J�[�\���N���X
class Cursor:

  # �N���X�ϐ� - �p�^�[����`
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

  # �N���X�ϐ� - �p���b�g��`
  CURSOR_PALETTE = ( 0b11100_11100_10000_0 )

  # �R���X�g���N�^
  def __init__(self, board_pos, cursor_pos):

    # Sprite �Q��
    self.sprite = x68k.Sprite()

    # ��ʒu
    self.board_x = board_pos[0] + 16 + int((Board.GRID_WIDTH - 32)/2)
    self.board_y = board_pos[1] + 16 + Board.GRID_HEIGHT - 4

    # �X�v���C�g������
    self.sprite.init()
    self.sprite.clr()
    self.sprite.defcg(0, Cursor.CURSOR_PATTERN, 1)
    self.sprite.palet(1, Cursor.CURSOR_PALETTE, 1)
    self.sprite.disp()

    # �����ʒu
    self.pos_x = cursor_pos[0]
    self.pos_y = cursor_pos[1]

  # �J�[�\���\�� (�X�v���C�g)
  def scroll(self, on=True, vsync=True):

    # �v���C�I���e�B ... 3:�\������ 0:�\�����Ȃ�
    priority = 3 if on else 0

    # vsync�҂�(�܂Ƃ߂ĕ����\������̂ł����ő҂�)
    if vsync:
      x68k.vsync()

    # �X�N���[��
    self.sprite.set(0, 
                    self.board_x + self.pos_x * Board.GRID_WIDTH, 
                    self.board_y + self.pos_y * Board.GRID_HEIGHT,
                    (1 << 8) | 0, priority, False)
    self.sprite.set(1, 
                    self.board_x + self.pos_x * Board.GRID_WIDTH + 16, 
                    self.board_y + self.pos_y * Board.GRID_HEIGHT,
                    (1 << 8) | 0, priority, False)

  # �J�[�\�����ړ�
  def move_left(self):
    self.pos_x = ( self.pos_x - 1 + 8 ) % 8
    self.scroll()

  # �J�[�\���E�ړ�
  def move_right(self):
    self.pos_x = ( self.pos_x + 1 ) % 8
    self.scroll()

  # �J�[�\����ړ�
  def move_up(self):
    self.pos_y = ( self.pos_y - 1 + 8 ) % 8
    self.scroll()

  # �J�[�\�����ړ�
  def move_down(self):
    self.pos_y = ( self.pos_y + 1 ) % 8
    self.scroll()

# �w��T�C�Y�E�w��ʒu��������C���[�W�̕\��
def put_image(pos, size, bitmap_image):
  gvram = x68k.GVRam()
  gvram.put(pos[0], pos[1], pos[0] + size[0] - 1, pos[1] + size[1] - 1, bitmap_image)

# 512x512x65536�C���[�W�t�@�C���̕\��
def load_full_image(image_file):
  with open(image_file, "rb") as f:
    
    # ��U�O���t�B�b�NOFF
    b = x68k.iocs(x68k.i.B_WPEEK, a1=0xe82600) & 0xffe0
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=b)

    # �t�@�C���̓��e��GVRAM�ɓ]��
    gvram = x68k.GVRam()
    for y in range(0, 512, 64):
      line_data = f.read(512 * 2 * 64)
      gvram.put(0, y, 511, y + 63, line_data)

    # �O���t�B�b�NON
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=(b | 0x0f))  

# 342x512x65536�C���[�W�t�@�C���̏c�X�N���[���\��
def load_portrait_image(image_file):
  with open(image_file, "rb") as f:
    
    # 384x256x65536���[�h (IPL-ROM 1.6 or CRTMOD16.X)
    x68k.crtmod(31, True)

    # �\���̈�O�ɂ��`����悤�ɃN���b�s���O�̈���L����
    x68k.iocs(x68k.i.WINDOW, d1=0, d2=0, d3=511, d4=511)

    # ��U�O���t�B�b�NOFF
    b = x68k.iocs(x68k.i.B_WPEEK, a1=0xe82600) & 0xffe0
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=b)

    # �t�@�C���̓��e��GVRAM�ɓ]��
    gvram = x68k.GVRam()
    for y in range(0, 512, 64):
      line_data = f.read(342 * 2 * 64)
      gvram.put(22, y, 363, y + 63, line_data)

    # �����X�N���[���ʒu
    x68k.iocs(x68k.i.SCROLL, d1=0, d2=0, d3=256)
    x68k.iocs(x68k.i.SCROLL, d1=1, d2=0, d3=256)
    x68k.iocs(x68k.i.SCROLL, d1=2, d2=0, d3=256)
    x68k.iocs(x68k.i.SCROLL, d1=3, d2=0, d3=256)

    # �O���t�B�b�NON
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=(b | 0x0f))  

    # ��ċz�u����
    time.sleep(2.000)

    # ���y���ݏc�X�N���[��
    for i in range(256):
      y = 255 - i
      x68k.vsync()
      x68k.iocs(x68k.i.SCROLL, d1=0, d2=0, d3=y)
      x68k.iocs(x68k.i.SCROLL, d1=1, d2=0, d3=y)
      x68k.iocs(x68k.i.SCROLL, d1=2, d2=0, d3=y)
      x68k.iocs(x68k.i.SCROLL, d1=3, d2=0, d3=y)

# ���C��
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

  # ��r�b�g�}�b�v�f�[�^�̃��[�h
  bitmap_black = None
  with open("koma_b.dat", "rb") as f:
    bitmap_black = f.read()
  bitmap_white = None
  with open("koma_w.dat", "rb") as f:
    bitmap_white = f.read()

  # COM��r�b�g�}�b�v�f�[�^�̃��[�h
  bitmap_com1 = None
  with open("com1.dat", "rb") as f:
    bitmap_com1 = f.read()

  # ���C�����[�v
  abort = False
  while abort is False:

    # �^�C�g����� -------------------------------------------------------------------------------

    # 512 x 512 x 65536 (31kHz) mode
    x68k.vsync()
    x68k.crtmod(12, True)

    # �X�v���C�g���e�L�X�g���O���t�B�b�N�̏��ɉ�ʃv���C�I���e�B��ύX����
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82500, d1=0b00000110_11100100)

    # �^�C�g���r�b�g�}�b�v�\��
    load_full_image("title3.dat")

    # �^�C�g�������\��
    print("\x1b[25;25H\x1b[37mPUSH SPACE KEY\x1b[m", end="")

    # �^�C�g���L�[�҂�
    while True:
      scan_code = ( x68k.iocs(x68k.i.B_KEYINP) >> 8 ) & 0x7f
      if scan_code == 0x01:       # esc key
        abort = True
        break
      elif scan_code == 0x35:     # space key
        break

    # ESC�������ꂽ�H
    if abort:
      break


    # �Q�[����� -------------------------------------------------------------------------------

    # �����
    if random.randint(0,1) == 0:
      # COM�����(��)
      color_computer = 1
      color_player = 2
    else:
      # COM�����(��)
      color_computer = 2
      color_player = 1

    # 512 x 512 x 65536 (31kHz) mode
    x68k.vsync()
    x68k.crtmod(12, True)

    # �X�v���C�g���O���t�B�b�N���e�L�X�g�̏��ɉ�ʃv���C�I���e�B��ύX����
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82500, d1=0b00001001_11100100)

    # ��U�O���t�B�b�N�E�e�L�X�g�E�X�v���C�gOFF
    b = x68k.iocs(x68k.i.B_WPEEK, a1=0xe82600) & 0xff00
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=b)

    # �{�[�h������
    board = Board((0, 4), bitmap_black, bitmap_white)
    board.repaint()

    # �J�[�\��������
    cursor = Cursor((0, 4), (0, 0))
    cursor.scroll()

    # �C���t�H���[�V�����\��
    print("\x1b[2;53H\x1b[mMicroReversi\x1b[m", end="")
    print("\x1b[3;53H\x1b[mPRO-68K     \x1b[m", end="")

    print("\x1b[6;53H\x1b[37mCOMPUTER\x1b[m", end="")
    if color_computer == 1:
      print("\x1b[16;53H��(���)", end="")
    else:
      print("\x1b[16;53H��(���)", end="")
    print("\x1b[18;53H2��", end="")
    
    print("\x1b[22;53H\x1b[37mPLAYER\x1b[m", end="")
    if color_player == 1:
      print("\x1b[24;53H��(���)", end="")
    else:
      print("\x1b[24;53H��(���)", end="")      
    print("\x1b[26;53H2��", end="")

    print("\x1b[32;1H[��������]:�}�X�I�� [RET/SP]:���u�� [p]:�p�X [ESC]:�I��", end="")

    # COM�r�b�g�}�b�v�\��
    put_image((408, 104), (104, 124), bitmap_com1)

    # �O���t�B�b�N�E�e�L�X�g�E�X�v���C�gON
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82600, d1=(b | 0x6f))

    # �Q�[�����[�v
    game_end = False      # �Q�[���I���t���O
    color_active = 1      # ���݂̎�Ԃ̐F
    pass_count = 0        # ���݂܂ł̃p�X��
    while game_end is False and abort is False:

      computer_placed = False
      player_placed = False

      if color_active == color_computer:
      
        # COM�̎��

        # �J�[�\��������
        cursor.scroll(False)

        # ���s�� �J�h(0,7,56,63)�͍ŗD��
        pos = [ 0, 7, 56, 63 ] + list(range(1,7)) + list(range(8,56)) + list(range(57,63))

        # ���s���̃V���b�t��
        for i in range(100):
          a = random.randint(0, 3)
          b = random.randint(0, 3)
          c = random.randint(4, 63)
          d = random.randint(4, 63)
          pos[ a ], pos[ b ] = pos[ b ], pos[ a ]
          pos[ c ], pos[ d ] = pos[ d ], pos[ c ]

        for p in pos:
          # �u���邩�H
          if board.place((p % 8, p // 8), color_computer):
            # �u����
            computer_placed = True
            break

      else:
        
        # �����̎��

        # flush key buffer
        x68k.dos(x68k.d.KFLUSH,pack('h',0))

        # �J�[�\����\������
        cursor.scroll(True)

        while player_placed is False and abort is False:

          # �L�[�{�[�h�ŃJ�[�\�����ړ������X�y�[�X�L�[�܂��̓��^�[���L�[�Ŋm��
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
                # �{���ɒu���Ƃ��Ȃ��H
                placeable = False
                for i in range(64):
                  if len(board.get_placeable_directions((i % 8, i // 8), color_player)) > 0:
                    placeable = True
                    break
                # �{���ɒu���Ƃ���Ȃ������̂Ńp�X
                if placeable is False:
                  pass_button = True
                  break

          # ESC�L�[�������ꂽ�H
          if abort:
            break

          # �p�X�L��
          if pass_button:
            break

          # �J�[�\���ʒu�ɖ{���ɂ�����H
          if board.place((cursor.pos_x, cursor.pos_y), color_player):
            # �u����
            player_placed = True
            break

      # �u�����ꍇ
      if computer_placed or player_placed:

        # �����\���X�V
        counts = board.count()
        if color_computer == 1:
          print(f"\x1b[18;53H{counts[0]}�� ", end="")
          print(f"\x1b[26;53H{counts[1]}�� ", end="")
        else:
          print(f"\x1b[18;53H{counts[1]}�� ", end="")
          print(f"\x1b[26;53H{counts[0]}�� ", end="")

        # �p�[�t�F�N�g�Q�[���H
        if counts[0] == 0 or counts[1] == 0:
          game_end = True
          break          

        # �����u���ꏊ�Ȃ��H
        if counts[0] + counts[1] == 64:
          game_end = True
          break

        # �p�X�񐔃��Z�b�g
        pass_count = 0

      else:

        # �p�X��2�񑱂�����I��
        pass_count += 1
        if pass_count >= 2:
          game_end = True
          break

      # ��Ԍ��
      if color_active == 1:
        color_active = 2
      else:
        color_active = 1

    # 1�Q�[���I��
    if abort is False:

      # ���ʕ\��
      computer_win = None
      counts = board.count()
      if counts[0] > counts[1]:
        computer_win = (color_computer == 1)
        print("\x1b[32;1H���̏����ł�\x1b[K", end="")
      elif counts[0] < counts[1]:
        computer_win = (color_computer == 2)
        print("\x1b[32;1H���̏����ł�\x1b[K", end="")
      else:
        print("\x1b[32;1H���������ł�\x1b[K", end="")      

      # 3�b�҂�
      time.sleep(3.000)

      # �r�W���A���V�[��
      if computer_win is None:
        # ���������Ȃ牽���Ȃ�
        pass
      elif computer_win:
        # COM�̏���
        load_portrait_image(f"win{random.randint(1,2)}.dat")
      else:
        # COM�̕���
        load_portrait_image(f"lose{random.randint(1,2)}.dat")

      # �����\��
      print("\x1b[2;2H\x1b[37mPUSH ANY KEY\x1b[m", end="")

      # flush key buffer
      x68k.dos(x68k.d.KFLUSH,pack('h',0))

      # �L�[�҂�
      while True:
        scan_code = ( x68k.iocs(x68k.i.B_KEYINP) >> 8 ) & 0x7f
        if scan_code != 0:
          break

  # �I������
  
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
  