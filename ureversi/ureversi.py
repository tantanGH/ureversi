import x68k
import random
import time
import sys
from uctypes import addressof
from struct import pack

# �o�[�W����
VERSION = const("2023.04.30")

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
  def is_placeable(self, pos, color):
    if self.board[ pos[0] + pos[1] * 8 ] == 0:
      return True
    else:
      return False

  # ���u��
  def place(self, pos, color):
    self.board[ pos[0] + pos[1] * 8 ] = (-1) * color

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

# 512x512x65536�C���[�W�t�@�C���̕\��
def load_image(image_file):
  with open(image_file, "rb") as f:
    gvram = x68k.GVRam()
    for y in range(0, 512, 64):
      line_data = f.read(512 * 2 * 64)
      gvram.put(0, y, 511, y + 63, line_data)

# ���C��
def main():

  # randomize
  random.seed(int(time.time() * 10))

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
  if bitmap_black is None or bitmap_white is None:
    print("error: data load error.")
    sys.exit(1)


  # ���C�����[�v
  abort = False
  while abort is False:

    # �^�C�g�����

    # 512 x 512 x 65536 (31kHz) mode
    x68k.vsync()
    x68k.crtmod(12, True)

    # �X�v���C�g���e�L�X�g���O���t�B�b�N�̏��ɉ�ʃv���C�I���e�B��ύX����
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82500, d1=0b00000110_11100100)

    # �^�C�g���r�b�g�}�b�v�\��
    load_image("title3.dat")

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


    # �Q�[�����

    # 512 x 512 x 65536 (31kHz) mode
    x68k.vsync()
    x68k.crtmod(12, True)

    # �X�v���C�g���O���t�B�b�N���e�L�X�g�̏��ɉ�ʃv���C�I���e�B��ύX����
    x68k.vsync()
    x68k.iocs(x68k.i.B_WPOKE, a1=0xe82500, d1=0b00001001_11100100)

    # �{�[�h������
    board = Board((0, 0), bitmap_black, bitmap_white)
    board.repaint()

    # �J�[�\��������
    cursor = Cursor((0, 0), (0, 0))
    cursor.scroll()

    # �C���t�H���[�V�����\��
    print("\x1b[2;53H\x1b[mMicroReversi\x1b[m", end="")
    print("\x1b[3;53H\x1b[mPRO-68K     \x1b[m", end="")

    print("\x1b[6;53H\x1b[37mCOMPUTER\x1b[m", end="")
    print("\x1b[8;53H��(���)", end="")
    print("\x1b[10;53H2��", end="")
    
    print("\x1b[14;53H\x1b[37mPLAYER\x1b[m", end="")
    print("\x1b[16;53H��(���)", end="")
    print("\x1b[18;53H2��", end="")

    print("\x1b[22;53H�J�[�\���L�[", end="")
    print("\x1b[23;53H�̏㉺���E��", end="")
    print("\x1b[24;53H�}�X��I����", end="")
    print("\x1b[25;53H���^�[���ŋ�", end="")
    print("\x1b[26;53H��u���܂�", end="")
    print("\x1b[29;53HESC�őޏo", end="")

    # �Q�[�����[�v
    abort = False
    while abort is False:

      # �L�[�{�[�h�ŃJ�[�\�����ړ������X�y�[�X�L�[�܂��̓��^�[���L�[�Ŋm��
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

      # ESC�L�[�������ꂽ�H
      if abort:
        break

      # �J�[�\���ʒu�ɖ{���ɂ�����H
      if board.is_placeable((cursor.pos_x, cursor.pos_y), 1):
        board.place((cursor.pos_x, cursor.pos_y), 1)
        board.repaint()
        counts = board.count()
        print(f"\x1b[10;53H{counts[1]}�� ", end="")
        print(f"\x1b[18;53H{counts[0]}�� ", end="")


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
  