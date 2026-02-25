import pygame
import random
import os
import sys

# دالة أساسية لضمان عمل الصور والأصوات بعد التحويل لـ EXE
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 400, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tri-Move: Ultra Edition")

WHITE, BLACK, GRAY = (245, 245, 245), (20, 20, 20), (180, 180, 180)
GREEN, BLUE, RED = (46, 204, 113), (52, 152, 219), (231, 76, 60)
GOLD = (241, 196, 15)

grid_color, ui_text_color = BLACK, BLACK
player_score, ai_score = 0, 0
MARGIN = 50
CELL_SIZE = (WIDTH - 2 * MARGIN) // 3

difficulty, theme_choice = 0, None
board = [2, 2, 2, 0, 0, 0, 1, 1, 1] 
selected_index, turn, game_over = None, "PLAYER", False
computer_timer, animating, anim_piece = 0, False, None
moved_indices_p = {6: False, 7: False, 8: False}
moved_indices_c = {0: False, 1: False, 2: False}
assets = {}

def load_theme_assets(theme):
    global assets, grid_color, ui_text_color
    path = theme.lower()
    try:
        raw_bg = None
        if theme == 'pink':
            raw_bg = pygame.image.load(resource_path(os.path.join(path, "pink_bg.jpg")))
            assets['p1'] = pygame.image.load(resource_path(os.path.join(path, "man.png")))
            assets['p2'] = pygame.image.load(resource_path(os.path.join(path, "profile.png")))
            grid_color, ui_text_color = (255, 182, 193), (255, 20, 147)
        elif theme == 'cartoon':
            assets['p1'] = pygame.image.load(resource_path(os.path.join(path, "leonardo.png")))
            assets['p2'] = pygame.image.load(resource_path(os.path.join(path, "penguin.png")))
            grid_color, ui_text_color = (50, 50, 50), BLACK
        elif theme == 'chess':
            assets['p1'] = pygame.image.load(resource_path(os.path.join(path, "knight.png")))
            assets['p2'] = pygame.image.load(resource_path(os.path.join(path, "rook.png")))
            grid_color, ui_text_color = (60, 60, 60), (40, 40, 40)

        if raw_bg: assets['bg'] = pygame.transform.smoothscale(raw_bg, (WIDTH, HEIGHT))
        else: assets['bg'] = None
        for key in ['p1', 'p2']:
            assets[key] = pygame.transform.smoothscale(assets[key], (CELL_SIZE-20, CELL_SIZE-20))
    except: pass

def get_cell_center(index):
    row, col = index // 3, index % 3
    return (MARGIN + col * CELL_SIZE + 10, MARGIN + row * CELL_SIZE + 10)

def start_move_anim(piece_img, start_idx, end_idx):
    global animating, anim_piece
    animating, anim_piece = True, {'img': piece_img, 'start': get_cell_center(start_idx), 'end': get_cell_center(end_idx), 'progress': 0}

def play_sound(sound_name):
    try:
        s = pygame.mixer.Sound(resource_path(f"{sound_name}.wav"))
        s.set_volume(0.15); s.play()
    except: pass

def check_win(b, mp, mc):
    p_ready, c_ready = all(mp.values()), all(mc.values())
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for p in wins:
        if b[p[0]] == b[p[1]] == b[p[2]] != 0:
            if b[p[0]] == 1 and p_ready: return 1
            if b[p[0]] == 2 and c_ready: return 2
    return None

def minimax(b, mp, mc, depth, is_max):
    res = check_win(b, mp, mc)
    if res == 2: return 10 - depth
    if res == 1: return depth - 10
    if depth >= 4: return 0 
    if is_max:
        best = -100
        pieces = [i for i, v in enumerate(b) if v == 2]
        empty = [i for i, v in enumerate(b) if v == 0]
        for p in pieces:
            for e in empty:
                b[p], b[e] = 0, 2
                nmc = mc.copy(); nmc[p] = True
                score = minimax(b, mp, nmc, depth + 1, False)
                b[p], b[e] = 2, 0; best = max(score, best)
        return best
    else:
        best = 100
        pieces = [i for i, v in enumerate(b) if v == 1]
        empty = [i for i, v in enumerate(b) if v == 0]
        for p in pieces:
            for e in empty:
                b[p], b[e] = 0, 1
                nmp = mp.copy(); nmp[p] = True
                score = minimax(b, nmp, mc, depth + 1, True)
                b[p], b[e] = 1, 0; best = min(score, best)
        return best

def computer_ai():
    pieces = [i for i, v in enumerate(board) if v == 2]
    empty = [i for i, v in enumerate(board) if v == 0]
    if difficulty == 3:
        best_val, best_move = -100, None
        for p in pieces:
            for e in empty:
                board[p], board[e] = 0, 2
                nmc = moved_indices_c.copy(); nmc[p] = True
                val = minimax(board, moved_indices_p, nmc, 0, False)
                board[p], board[e] = 2, 0
                if val > best_val: best_val, best_move = val, (p, e)
        return best_move
    return random.choice(pieces), random.choice(empty)

def draw_text(text, y, size=30, color=BLACK, bold=True, center_x=WIDTH//2):
    font = pygame.font.SysFont("Arial", size, bold=bold)
    img = font.render(text, True, color)
    SCREEN.blit(img, (center_x - img.get_width()//2, y))

def draw_menu_btn(text, y, color):
    rect = pygame.Rect(WIDTH//2 - 110, y, 220, 55)
    pygame.draw.rect(SCREEN, color, rect, border_radius=12)
    draw_text(text, y+12, 22, WHITE)
    return rect

def reset_game():
    global board, selected_index, turn, game_over, moved_indices_p, moved_indices_c, animating
    board = [2, 2, 2, 0, 0, 0, 1, 1, 1]
    selected_index, turn, game_over, animating = None, "PLAYER", False, False
    moved_indices_p = {6: False, 7: False, 8: False}
    moved_indices_c = {0: False, 1: False, 2: False}

running = True
clock = pygame.time.Clock()
while running:
    if difficulty == 0:
        SCREEN.fill(WHITE)
        draw_text("TRI-MOVE", 80, 50, BLACK)
        b1, b2, b3 = draw_menu_btn("EASY", 240, GREEN), draw_menu_btn("MEDIUM", 320, BLUE), draw_menu_btn("IMPOSSIBLE", 400, RED)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if b1.collidepoint(event.pos): difficulty = 1
                if b2.collidepoint(event.pos): difficulty = 2
                if b3.collidepoint(event.pos): difficulty = 3
    elif theme_choice is None:
        SCREEN.fill(WHITE)
        draw_text("SELECT THEME", 100, 35, BLACK)
        t1, t2, t3 = draw_menu_btn("Pink Style", 240, (255,105,180)), draw_menu_btn("Cartoon", 320, (255,165,0)), draw_menu_btn("Chess", 400, (100,100,100))
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn, tid in [(t1,'pink'), (t2,'cartoon'), (t3,'chess')]:
                    if btn.collidepoint(event.pos): theme_choice = tid; load_theme_assets(tid); reset_game()
    else:
        if assets.get('bg'): SCREEN.blit(assets['bg'], (0,0))
        else: SCREEN.fill(WHITE)
        if theme_choice == 'chess':
            for i in range(9):
                c = (255,255,255) if ((i//3) + (i%3)) % 2 == 0 else (200,200,200)
                pygame.draw.rect(SCREEN, c, (MARGIN+(i%3)*CELL_SIZE, MARGIN+(i//3)*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        draw_text(f"YOU: {player_score}", 15, 20, ui_text_color, center_x=WIDTH//4)
        draw_text(f"AI: {ai_score}", 15, 20, ui_text_color, center_x=3*WIDTH//4)
        for i in range(4):
            pygame.draw.line(SCREEN, grid_color, (MARGIN, MARGIN+i*CELL_SIZE), (WIDTH-MARGIN, MARGIN+i*CELL_SIZE), 2)
            pygame.draw.line(SCREEN, grid_color, (MARGIN+i*CELL_SIZE, MARGIN), (MARGIN+i*CELL_SIZE, MARGIN+3*CELL_SIZE), 2)
        for i, val in enumerate(board):
            r = pygame.Rect(MARGIN+(i%3)*CELL_SIZE, MARGIN+(i//3)*CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if i == selected_index: pygame.draw.rect(SCREEN, GOLD, r, 4, border_radius=10)
            if val != 0: SCREEN.blit(assets['p'+str(val)], (r.x+10, r.y+10))
        if animating:
            anim_piece['progress'] += 0.1
            p = anim_piece['progress']
            curr_x = anim_piece['start'][0] + (anim_piece['end'][0] - anim_piece['start'][0]) * p
            curr_y = anim_piece['start'][1] + (anim_piece['end'][1] - anim_piece['start'][1]) * p
            SCREEN.blit(anim_piece['img'], (curr_x, curr_y))
            if p >= 1: animating = False
        winner = check_win(board, moved_indices_p, moved_indices_c)
        if winner and not game_over:
            game_over = True
            if winner == 1: player_score += 1
            else: ai_score += 1
            play_sound("win" if winner == 1 else "lose")
        replay_btn, main_menu_btn = None, None
        if game_over:
            draw_text("VICTORY!" if winner == 1 else "DEFEAT!", HEIGHT-160, 40, ui_text_color)
            replay_btn = pygame.Rect(WIDTH//2 - 110, HEIGHT-90, 100, 45)
            pygame.draw.rect(SCREEN, GREEN, replay_btn, border_radius=10)
            draw_text("REPLAY", HEIGHT-80, 18, WHITE, center_x=WIDTH//2-60)
            main_menu_btn = pygame.Rect(WIDTH//2 + 10, HEIGHT-90, 100, 45)
            pygame.draw.rect(SCREEN, GRAY, main_menu_btn, border_radius=10)
            draw_text("MENU", HEIGHT-80, 18, BLACK, center_x=WIDTH//2+60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN and not animating:
                if game_over:
                    if replay_btn and replay_btn.collidepoint(event.pos): reset_game()
                    if main_menu_btn and main_menu_btn.collidepoint(event.pos): difficulty, theme_choice = 0, None; reset_game()
                elif not game_over and turn == "PLAYER":
                    for i in range(9):
                        r = pygame.Rect(MARGIN+(i%3)*CELL_SIZE, MARGIN+(i//3)*CELL_SIZE, CELL_SIZE, CELL_SIZE)
                        if r.collidepoint(event.pos):
                            if board[i] == 1: selected_index = i
                            elif board[i] == 0 and selected_index is not None:
                                start_move_anim(assets['p1'], selected_index, i)
                                board[selected_index], board[i] = 0, 1; play_sound("move")
                                if selected_index in moved_indices_p: moved_indices_p[selected_index] = True
                                selected_index, turn, computer_timer = None, "COMPUTER", pygame.time.get_ticks()
        if turn == "COMPUTER" and not game_over and not animating:
            if pygame.time.get_ticks() - computer_timer >= 600:
                res = computer_ai()
                if res:
                    p, e = res; start_move_anim(assets['p2'], p, e); board[p], board[e] = 0, 2; play_sound("move")
                    if p in moved_indices_c: moved_indices_c[p] = True
                    turn = "PLAYER"
    pygame.display.flip(); clock.tick(60)
pygame.quit()