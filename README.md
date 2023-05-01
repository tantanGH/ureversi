# ureversi

Micro Reversi PRO-68K for X680x0/MicroPython

yunk氏の [MicroPython for X680x0](https://github.com/yunkya2/micropython-x68k/tree/port-x68k/ports/x68k) を使って実装したリバーシ(オセロ)です。

<img src='images/ureversi1.png' width='800'/>

<img src='images/ureversi2.png' width='800'/>

---

### インストール

- [MicroPython for X680x0](https://github.com/yunkya2/micropython-x68k/tree/port-x68k/ports/x68k) の最新版を導入しておく。

- [ureversi.lzh](https://github.com/tantanGH/ureverse/raw/main/ureversi.lzh) をダウンロードし、新規ディレクトリに展開する。

- 展開したディレクトリにカレントディレクトリを移し、`*.dat` ファイルと `ureversi.py` が存在するのを確認して、以下のコマンドで起動する。

        micropython ureversi.py

---

### X68000Z向け起動用XDF

- [X68Z_MicroReversi_20230501.XDF](https://github.com/tantanGH/ureverse/raw/main/xdf/X68Z_MicroReversi_20230501.XDF)

RAMDISKを作成し、そこに展開を行います。

X68000Z EAK 以外の環境で起動した場合は、最初に見つかったRAMDISKドライブに書き込みを行いますので注意してください。

---


<img src='images/ureversi3.png' width='800'/>



