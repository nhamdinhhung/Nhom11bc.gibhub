import sys
import time
import math
import threading
import pygame
from src.board import Board, BOARD_SIZE, PLAYER, AI, EMPTY
from src.ai import AIPlayer, ALGO_MINIMAX, ALGO_ALPHABETA

# ── Màu sắc ──────────────────────────────────────────────────
C_BG          = (13, 17, 23)
C_SURFACE     = (22, 28, 36)
C_SURFACE2    = (30, 38, 50)
C_BORDER      = (48, 60, 78)
C_BORDER2     = (68, 85, 108)
C_BOARD_BG    = (16, 22, 32)
C_GRID        = (35, 48, 65)
C_GRID_BRIGHT = (55, 72, 98)

C_X           = (80, 180, 255)   # X = xanh dương
C_X_GLOW      = (30, 100, 180)
C_O           = (230, 235, 245)  # O = trắng ngà
C_O_GLOW      = (90, 100, 125)

C_WIN_GOLD    = (255, 210, 50)
C_TEXT        = (215, 228, 245)
C_TEXT2       = (125, 148, 175)
C_TEXT3       = (65, 85, 110)
C_BTN         = (32, 42, 60)
C_BTN_HOV     = (46, 60, 85)
C_BTN_ACT     = (80, 180, 255)
C_BTN_ACT_T   = (10, 15, 25)
C_ACCENT      = (80, 180, 255)
C_ACCENT2     = (200, 210, 230)
C_WIN_CLR     = (80, 210, 140)
C_LOSE_CLR    = (255, 100, 80)
C_DRAW_CLR    = (200, 175, 70)

# ── Layout ────────────────────────────────────────────────────
CELL     = 60           # ô to hơn
MARGIN   = 44
BOARD_PX = BOARD_SIZE * CELL   # 9×60 = 540
PANEL_W  = 270
GAP      = 24
WIN_W    = MARGIN*2 + BOARD_PX + PANEL_W + GAP   # 44+44+540+270+24 = 922
WIN_H    = MARGIN*2 + BOARD_PX + 130             # tăng thêm để chứa hàng algo
BX       = MARGIN
BY       = MARGIN + 52
PX       = BX + BOARD_PX + GAP
PY       = BY

MODE_PVA = "pva"
MODE_AVA = "ava"

# Panel rows — tất cả tính từ PY, không overlap
R_MODE   = 0           # mode buttons
R_NEW    = 44          # ván mới
R_UNDO   = 86          # đi lại / dừng
R_STATUS = 128         # status bar
R_D1_LBL  = 168        # depth label row 1
R_D1_BTN  = 184        # depth buttons row 1
R_A1_LBL  = 218        # algo label row 1
R_A1_BTN  = 234        # algo buttons row 1
R_D2_LBL  = 272        # depth label row 2 (AVA only)
R_D2_BTN  = 288        # depth buttons row 2 (AVA only)
R_A2_LBL  = 322        # algo label row 2 (AVA only)
R_A2_BTN  = 338        # algo buttons row 2 (AVA only)
R_SCORE_PVA = 272      # score cards (PVA)
R_SCORE_AVA = 376      # score cards (AVA — after both algo rows)
R_HIST_PVA  = 342      # history start (PVA)
R_HIST_AVA  = 446      # history start (AVA)


class AnimPiece:
    def __init__(self, r, c, player):
        self.r = r; self.c = c; self.player = player
        self.frame = 0; self.MAX = 14
    @property
    def t(self): return min(1.0, self.frame / self.MAX)
    @property
    def done(self): return self.frame >= self.MAX


class Btn:
    def __init__(self, rect, label, tag=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.tag = tag

    def draw(self, surf, font, hov=False, active=False):
        if active:  bg, fg, brd = C_BTN_ACT, C_BTN_ACT_T, C_BTN_ACT
        elif hov:   bg, fg, brd = C_BTN_HOV, C_TEXT,  C_BORDER2
        else:       bg, fg, brd = C_BTN,     C_TEXT2, C_BORDER
        pygame.draw.rect(surf, bg,  self.rect, border_radius=9)
        pygame.draw.rect(surf, brd, self.rect, 1, border_radius=9)
        t = font.render(self.label, True, fg)
        surf.blit(t, t.get_rect(center=self.rect.center))

    def hit(self, p): return self.rect.collidepoint(p)
    def clicked(self, p, ev): return ev.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(p)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Cờ Caro — AI Edition")
        self.clock = pygame.time.Clock()
        self._fonts()

        self.board      = Board()
        self.ai1        = AIPlayer(depth=2, algo=ALGO_ALPHABETA)
        self.ai2        = AIPlayer(depth=2, algo=ALGO_ALPHABETA)
        self.scores     = {PLAYER: 0, "draw": 0, AI: 0}
        self.move_log   = []
        self.move_count = 0
        self.cur        = PLAYER
        self.game_over  = False
        self.winning    = []
        self.last_move  = None
        self.thinking   = False
        self.mode       = MODE_PVA
        self.depth1     = 2
        self.depth2     = 2
        self.algo1      = ALGO_ALPHABETA
        self.algo2      = ALGO_ALPHABETA
        self.ava_run    = False
        self.ava_pause  = False
        self.anims      = []
        self.win_pulse  = 0
        self.h_scroll   = 0
        self.nodes      = 0
        self._build_btns()

    def _fonts(self):
        for attr, sz in [("fnt_title",28),("fnt_lg",22),("fnt_md",16),
                         ("fnt_sm",14),("fnt_xs",12),("fnt_num",10)]:
            try:    setattr(self, attr, pygame.font.SysFont("bahnschrift", sz))
            except: setattr(self, attr, pygame.font.SysFont(None, sz+4))

    def _build_btns(self):
        pw = PANEL_W - 10
        hw = (pw - 8) // 2

        self.btn_pva   = Btn((PX,      PY+R_MODE, hw, 36), "Người vs AI", MODE_PVA)
        self.btn_ava   = Btn((PX+hw+8, PY+R_MODE, hw, 36), "🤖 AI vs AI",  MODE_AVA)
        self.btn_new   = Btn((PX,      PY+R_NEW,  pw, 36), "▶  Ván mới")
        self.btn_undo  = Btn((PX,      PY+R_UNDO, pw, 34), "↩  Đi lại")
        self.btn_pause = Btn((PX,      PY+R_UNDO, pw, 34), "⏸  Dừng")

        self.d_btns1 = [Btn((PX+i*56, PY+R_D1_BTN, 48, 28), str(d), d) for i,d in enumerate([1,2,3,4])]
        self.d_btns2 = [Btn((PX+i*56, PY+R_D2_BTN, 48, 28), str(d), d) for i,d in enumerate([1,2,3,4])]

        ab_w = (PANEL_W - 10 - 8) // 2
        self.a_btns1 = [
            Btn((PX,        PY+R_A1_BTN, ab_w, 28), "Minimax",   ALGO_MINIMAX),
            Btn((PX+ab_w+8, PY+R_A1_BTN, ab_w, 28), "Alpha-Beta", ALGO_ALPHABETA),
        ]
        self.a_btns2 = [
            Btn((PX,        PY+R_A2_BTN, ab_w, 28), "Minimax",   ALGO_MINIMAX),
            Btn((PX+ab_w+8, PY+R_A2_BTN, ab_w, 28), "Alpha-Beta", ALGO_ALPHABETA),
        ]

    # ── Main loop ────────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(60)
            mp = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                self._handle(ev, mp)
            self._tick()
            self._draw(mp)

    def _tick(self):
        for a in self.anims:
            if not a.done: a.frame += 1
        self.anims = [a for a in self.anims if not a.done]
        if self.winning:
            self.win_pulse = (self.win_pulse + 4) % 360

    # ── Events ───────────────────────────────────────────────
    def _handle(self, ev, mp):
        if self.btn_pva.clicked(mp, ev): self._set_mode(MODE_PVA)
        if self.btn_ava.clicked(mp, ev): self._set_mode(MODE_AVA)
        if self.btn_new.clicked(mp, ev): self._new_game()

        if self.mode == MODE_PVA:
            if self.btn_undo.clicked(mp, ev): self._undo()
        else:
            if self.btn_pause.clicked(mp, ev):
                self.ava_pause = not self.ava_pause

        for b in self.d_btns1:
            if b.clicked(mp, ev): self.depth1 = b.tag; self.ai1.set_depth(b.tag)
        for b in self.d_btns2:
            if b.clicked(mp, ev): self.depth2 = b.tag; self.ai2.set_depth(b.tag)
        for b in self.a_btns1:
            if b.clicked(mp, ev): self.algo1 = b.tag; self.ai1.set_algo(b.tag)
        for b in self.a_btns2:
            if b.clicked(mp, ev): self.algo2 = b.tag; self.ai2.set_algo(b.tag)

        if ev.type == pygame.MOUSEWHEEL:
            self.h_scroll = max(0, self.h_scroll - ev.y)

        if ev.type == pygame.MOUSEBUTTONDOWN and self.mode == MODE_PVA:
            if not self.game_over and not self.thinking and self.cur == PLAYER:
                c = (mp[0]-BX) // CELL
                r = (mp[1]-BY) // CELL
                if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE:
                    self._player_move(r, c)

    # ── Game logic ───────────────────────────────────────────
    def _set_mode(self, mode):
        self.mode = mode; self.ava_run = False; self.ava_pause = False
        self._new_game()

    def _new_game(self):
        if self.thinking: return
        self.board.reset()
        self.move_log = []; self.move_count = 0
        self.cur = PLAYER; self.game_over = False
        self.winning = []; self.last_move = None
        self.h_scroll = 0; self.anims = []; self.nodes = 0
        self.ava_run = False; self.ava_pause = False
        if self.mode == MODE_AVA:
            self.ava_run = True
            threading.Thread(target=self._ava_loop, daemon=True).start()

    def _player_move(self, r, c):
        if not self.board.is_valid(r, c): return
        self._make_move(r, c, PLAYER, 0)
        if self._check_end(r, c, PLAYER): return
        self.cur = AI; self.thinking = True
        threading.Thread(target=self._ai_turn, args=(self.ai2, AI), daemon=True).start()

    def _ai_turn(self, ai_obj, player):
        t0 = time.time()
        move = ai_obj.get_best_move(self.board)
        elapsed = time.time() - t0
        self.nodes = ai_obj.nodes_evaluated
        if move:
            self._make_move(move[0], move[1], player, elapsed)
            if not self._check_end(move[0], move[1], player):
                self.cur = PLAYER
        self.thinking = False

    def _ava_loop(self):
        while self.ava_run:
            if self.game_over: break
            while self.ava_pause and self.ava_run: time.sleep(0.05)
            if not self.ava_run: break
            ai_obj = self.ai1 if self.cur == PLAYER else self.ai2
            player = self.cur
            self.thinking = True
            t0 = time.time()
            move = ai_obj.get_best_move(self.board)
            elapsed = time.time() - t0
            self.nodes = ai_obj.nodes_evaluated
            self.thinking = False
            if not move or not self.ava_run: break
            self._make_move(move[0], move[1], player, elapsed)
            if self._check_end(move[0], move[1], player): break
            self.cur = AI if player == PLAYER else PLAYER
            time.sleep(0.35)

    def _make_move(self, r, c, player, elapsed):
        self.board.place(r, c, player)
        self.move_count += 1
        self.last_move = (r, c)
        self.move_log.append((self.move_count, r, c, player, elapsed))
        self.h_scroll = max(0, len(self.move_log) - 12)
        self.anims.append(AnimPiece(r, c, player))

    def _check_end(self, r, c, player):
        win = self.board.check_win(r, c, player)
        if win: self.winning = win; self._end("win", player); return True
        if self.board.is_full(): self._end("draw", None); return True
        return False

    def _end(self, result, player):
        self.game_over = True; self.ava_run = False
        if result == "draw": self.scores["draw"] += 1
        else: self.scores[player] += 1

    def _undo(self):
        if self.thinking: return
        self.game_over = False; self.winning = []
        if self.cur == PLAYER and len(self.move_log) >= 2:
            for _ in range(2):
                self.board.undo(); self.move_log.pop(); self.move_count -= 1
            self.last_move = (self.move_log[-1][1], self.move_log[-1][2]) if self.move_log else None
            self.anims = []

    # ── Draw ─────────────────────────────────────────────────
    def _draw(self, mp):
        self.screen.fill(C_BG)
        self._draw_deco()
        self._draw_title()
        self._draw_board(mp)
        self._draw_panel(mp)
        pygame.display.flip()

    def _draw_deco(self):
        for pos, clr in [((0,0), C_X_GLOW), ((WIN_W, WIN_H), C_O_GLOW)]:
            s = pygame.Surface((300,300), pygame.SRCALPHA)
            pygame.draw.circle(s, (*clr, 16), (150,150), 150)
            self.screen.blit(s, (pos[0]-150, pos[1]-150))

    def _draw_title(self):
        t1 = self.fnt_title.render("CARO", True, C_ACCENT)
        t2 = self.fnt_sm.render("AI EDITION", True, C_TEXT3)
        self.screen.blit(t1, (BX, 10))
        self.screen.blit(t2, (BX + t1.get_width() + 12, 22))
        pygame.draw.line(self.screen, C_BORDER, (BX, 48), (BX+BOARD_PX, 48), 1)

    def _draw_board(self, mp):
        board_rect = pygame.Rect(BX, BY, BOARD_PX, BOARD_PX)
        pygame.draw.rect(self.screen, C_BOARD_BG, board_rect, border_radius=10)

        for i in range(BOARD_SIZE+1):
            clr = C_GRID_BRIGHT if i % 3 == 0 else C_GRID
            pygame.draw.line(self.screen, clr, (BX+i*CELL, BY), (BX+i*CELL, BY+BOARD_PX))
            pygame.draw.line(self.screen, clr, (BX, BY+i*CELL), (BX+BOARD_PX, BY+i*CELL))

        # Center dot
        cc = BOARD_SIZE // 2
        pygame.draw.circle(self.screen, C_GRID_BRIGHT,
                           (BX+cc*CELL+CELL//2, BY+cc*CELL+CELL//2), 4)

        # Win glow pulse
        wp = int(140 + 80*math.sin(math.radians(self.win_pulse)))
        for (wr, wc) in self.winning:
            s = pygame.Surface((CELL-2, CELL-2), pygame.SRCALPHA)
            s.fill((*C_WIN_GOLD, wp))
            self.screen.blit(s, (BX+wc*CELL+1, BY+wr*CELL+1))

        # Last move
        if self.last_move and not self.winning:
            lr, lc = self.last_move
            s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
            s.fill((255,255,255,18))
            self.screen.blit(s, (BX+lc*CELL, BY+lr*CELL))

        # Hover
        if self.mode == MODE_PVA and not self.game_over and not self.thinking and self.cur == PLAYER:
            hc = (mp[0]-BX)//CELL; hr = (mp[1]-BY)//CELL
            if 0 <= hr < BOARD_SIZE and 0 <= hc < BOARD_SIZE and self.board.grid[hr][hc] == EMPTY:
                s = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
                s.fill((*C_ACCENT, 35))
                self.screen.blit(s, (BX+hc*CELL, BY+hr*CELL))

        # Pieces — KHÔNG hiện số bước
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                val = self.board.grid[r][c]
                if val == EMPTY: continue
                cx_ = BX + c*CELL + CELL//2
                cy_ = BY + r*CELL + CELL//2
                color = C_X if val == PLAYER else C_O
                gclr  = C_X_GLOW if val == PLAYER else C_O_GLOW
                char  = "✕" if val == PLAYER else "○"

                anim = next((a for a in self.anims if a.r==r and a.c==c), None)
                scale = 1.0
                if anim:
                    t = anim.t
                    scale = 1.0 + 0.38*math.sin(t*math.pi)*(1-t*0.35)

                gr = int(CELL*0.40*scale)
                gs = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
                pygame.draw.circle(gs, (*gclr, 55), (gr,gr), gr)
                self.screen.blit(gs, (cx_-gr, cy_-gr))

                sz = max(14, int(30*scale))
                try:    f = pygame.font.SysFont("bahnschrift", sz, bold=True)
                except: f = pygame.font.SysFont(None, sz+4, bold=True)
                pt = f.render(char, True, color)
                self.screen.blit(pt, pt.get_rect(center=(cx_, cy_)))

        # Axis labels
        for i in range(BOARD_SIZE):
            cl = self.fnt_xs.render(chr(65+i), True, C_TEXT3)
            rl = self.fnt_xs.render(str(i+1),  True, C_TEXT3)
            self.screen.blit(cl, (BX+i*CELL+CELL//2-cl.get_width()//2, BY-18))
            self.screen.blit(rl, (BX-26, BY+i*CELL+CELL//2-rl.get_height()//2))

        pygame.draw.rect(self.screen, C_BORDER2, board_rect, 1, border_radius=10)

    def _draw_panel(self, mp):
        pw = PANEL_W - 10

        # ── 1. Mode buttons ──────────────────────────────────
        self.btn_pva.draw(self.screen, self.fnt_sm, self.btn_pva.hit(mp), self.mode==MODE_PVA)
        self.btn_ava.draw(self.screen, self.fnt_sm, self.btn_ava.hit(mp), self.mode==MODE_AVA)

        # ── 2. Ván mới ───────────────────────────────────────
        self.btn_new.draw(self.screen, self.fnt_md, self.btn_new.hit(mp))

        # ── 3. Đi lại / Dừng ─────────────────────────────────
        if self.mode == MODE_PVA:
            self.btn_undo.draw(self.screen, self.fnt_sm, self.btn_undo.hit(mp))
        else:
            self.btn_pause.label = "▶  Tiếp" if self.ava_pause else "⏸  Dừng"
            self.btn_pause.draw(self.screen, self.fnt_sm, self.btn_pause.hit(mp))

        # ── 4. Status bar ────────────────────────────────────
        if self.game_over:
            if self.winning:
                w = self.move_log[-1][3] if self.move_log else None
                if self.mode == MODE_PVA:
                    txt = "🎉 Bạn thắng!" if w==PLAYER else "💻 Máy thắng!"
                else:
                    txt = "🔵 X (AI-1) thắng!" if w==PLAYER else "⚪ O (AI-2) thắng!"
                clr = C_WIN_CLR if (w==PLAYER and self.mode==MODE_PVA) else C_LOSE_CLR
            else:
                txt = "🤝 Hòa!"; clr = C_DRAW_CLR
        elif self.thinking:
            dots = "." * (int(time.time()*3) % 4)
            txt = f"Đang suy nghĩ{dots}"; clr = C_TEXT2
        else:
            if self.mode == MODE_PVA:
                txt = "Lượt của bạn (X)" if self.cur==PLAYER else "Máy đang tính..."
                clr = C_ACCENT if self.cur==PLAYER else C_ACCENT2
            else:
                pn = "X (AI-1)" if self.cur==PLAYER else "O (AI-2)"
                txt = f"Lượt: {pn}" + ("  ⏸" if self.ava_pause else "")
                clr = C_ACCENT if self.cur==PLAYER else C_ACCENT2

        sr = pygame.Rect(PX, PY+R_STATUS, pw, 32)
        pygame.draw.rect(self.screen, C_SURFACE2, sr, border_radius=7)
        pygame.draw.rect(self.screen, C_BORDER, sr, 1, border_radius=7)
        st = self.fnt_sm.render(txt, True, clr)
        self.screen.blit(st, st.get_rect(center=sr.center))

        # ── 5. Depth AI-1 ────────────────────────────────────
        lbl1 = "Độ sâu AI:" if self.mode==MODE_PVA else "Độ sâu X (AI-1):"
        self._lbl(PX, PY+R_D1_LBL, lbl1)
        for b in self.d_btns1:
            b.draw(self.screen, self.fnt_sm, b.hit(mp), b.tag==self.depth1)

        # ── 6. Algo AI-1 ─────────────────────────────────────
        lbl_a1 = "Thuật toán AI:" if self.mode==MODE_PVA else "Thuật toán X (AI-1):"
        self._lbl(PX, PY+R_A1_LBL, lbl_a1)
        for b in self.a_btns1:
            b.draw(self.screen, self.fnt_sm, b.hit(mp), b.tag==self.algo1)

        # ── 7. Depth + Algo AI-2 (chỉ AVA) ──────────────────
        if self.mode == MODE_AVA:
            self._lbl(PX, PY+R_D2_LBL, "Độ sâu O (AI-2):")
            for b in self.d_btns2:
                b.draw(self.screen, self.fnt_sm, b.hit(mp), b.tag==self.depth2)
            self._lbl(PX, PY+R_A2_LBL, "Thuật toán O (AI-2):")
            for b in self.a_btns2:
                b.draw(self.screen, self.fnt_sm, b.hit(mp), b.tag==self.algo2)

        # ── 7. Score cards ───────────────────────────────────
        sc_y = PY + (R_SCORE_AVA if self.mode==MODE_AVA else R_SCORE_PVA)
        cards = [
            ("X" + (" (Bạn)" if self.mode==MODE_PVA else " AI-1"), self.scores[PLAYER], C_X),
            ("Hòa",                                                  self.scores["draw"], C_TEXT2),
            ("O" + (" (Máy)" if self.mode==MODE_PVA else " AI-2"),  self.scores[AI],     C_O),
        ]
        cw = (pw - 8) // 3
        for i, (lb, val, clr) in enumerate(cards):
            cr = pygame.Rect(PX+i*(cw+4), sc_y, cw, 58)
            pygame.draw.rect(self.screen, C_SURFACE, cr, border_radius=8)
            pygame.draw.rect(self.screen, C_BORDER,  cr, 1, border_radius=8)
            pygame.draw.rect(self.screen, clr,
                             pygame.Rect(cr.x+1, cr.y+1, cr.w-2, 3), border_radius=2)
            lt = self.fnt_xs.render(lb,       True, C_TEXT3)
            vt = self.fnt_lg.render(str(val), True, clr)
            self.screen.blit(lt, lt.get_rect(centerx=cr.centerx, y=cr.y+10))
            self.screen.blit(vt, vt.get_rect(centerx=cr.centerx, y=cr.y+26))

        # ── 8. History panel ─────────────────────────────────
        hy = PY + (R_HIST_AVA if self.mode==MODE_AVA else R_HIST_PVA)
        hh = WIN_H - hy - 10
        if hh < 60: return
        hp = pygame.Rect(PX, hy, pw, hh)
        pygame.draw.rect(self.screen, C_SURFACE, hp, border_radius=8)
        pygame.draw.rect(self.screen, C_BORDER,  hp, 1, border_radius=8)

        hl = self.fnt_sm.render("Lịch sử nước đi", True, C_TEXT2)
        self.screen.blit(hl, (PX+10, hy+7))
        pygame.draw.line(self.screen, C_BORDER, (PX+6, hy+24), (PX+pw-6, hy+24), 1)

        ih  = 22
        vis = max(1, (hh-32)//ih)
        total = len(self.move_log)
        start = min(self.h_scroll, max(0, total-vis))
        shown = list(reversed(self.move_log))[start:start+vis]

        self.screen.set_clip(pygame.Rect(PX+4, hy+28, pw-8, hh-36))
        for idx, (num, r, c, player, elapsed) in enumerate(shown):
            iy = hy + 28 + idx*ih
            if num == self.move_count:
                pygame.draw.rect(self.screen, C_SURFACE2,
                                 pygame.Rect(PX+4, iy, pw-8, ih), border_radius=4)
            pc  = C_X   if player==PLAYER else C_O
            sym = "✕"   if player==PLAYER else "○"
            pos = f"{chr(65+c)}{r+1}"
            elt = f"{elapsed:.2f}s"
            self.screen.blit(self.fnt_xs.render(str(num), True, C_TEXT3), (PX+8,   iy+4))
            self.screen.blit(self.fnt_xs.render(sym,      True, pc),      (PX+32,  iy+4))
            self.screen.blit(self.fnt_xs.render(pos,      True, C_TEXT),  (PX+56,  iy+4))
            self.screen.blit(self.fnt_xs.render(elt,      True, C_TEXT3), (PX+130, iy+4))
        self.screen.set_clip(None)

    def _lbl(self, x, y, text):
        self.screen.blit(self.fnt_xs.render(text, True, C_TEXT3), (x, y))
