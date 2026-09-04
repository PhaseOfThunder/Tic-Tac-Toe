# This is the main file, program execution happens here
import random
from pyscript import when, document, window

grid = document.querySelectorAll(".slot")

start_screen = document.getElementById("start-screen")
win_screen = document.getElementById("win-screen")
lose_screen = document.getElementById("lose-screen")
tie_screen = document.getElementById("tie-screen")

# --- Sound effects ---
click_sfx = window.Audio.new("./resources/click.mp3")
game_over_sfx = window.Audio.new("./resources/game_over.mp3")

music = window.Audio.new("./resources/music.mp3")
music.loop = True
music.volume = 0.3

def play_sound(sound):
    """Play a sound from the start, even if it is already playing."""
    sound.currentTime = 0
    # play() rejects if the browser blocks autoplay; ignore that instead of
    # letting an unhandled promise rejection spam the console
    sound.play().catch(lambda error: None)

turnText = document.getElementById("turn")
turn = 1

PLAYER = "O"
COMPUTER = "X"

# "computer" plays the AI, "friend" is two people sharing one screen.
# Set for real when a mode button on the start screen is clicked.
game_mode = "computer"

# whose mark goes down next; only used in friend mode
current_mark = PLAYER

# every trio of slot indexes that forms a line: rows, columns, diagonals
WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6),             # diagonals
]

@when("click", "button")
def any_button_clicked(event):
    """Click sound for every button on the page."""
    play_sound(click_sfx)

@when("click", ".mode-button")
def mode_chosen(event):
    """Start the game in whichever mode the player picked."""
    global game_mode

    game_mode = event.target.dataset.mode
    print(f"playing against {game_mode}")

    # the click counts as user interaction, so audio is unblocked now
    music.play().catch(lambda error: None)

    start_screen.classList.remove("visible")
    update_turn_text()

@when("click", ".slot")
def slot_clicked_player(event):
    """Fill the clicked slot, then hand over to the computer or the friend."""
    global turn, current_mark

    slot = event.target
    if slot.textContent:
        return  # already taken, ignore the click

    if game_mode == "friend":
        # two people taking turns: O goes first, then X, then back again
        take_slot(slot, current_mark)

        winner = check_for_win()
        if winner:
            # O gets the gold screen, X gets the rose one
            screen = win_screen if winner == PLAYER else lose_screen
            show_end_screen(screen, f"{winner} Wins", "Nice one. Rematch?")
            return

        if board_is_full():
            show_end_screen(tie_screen)
            return

        current_mark = COMPUTER if current_mark == PLAYER else PLAYER
        turn += 1
        update_turn_text()
        return

    # --- playing the computer ---
    take_slot(slot, PLAYER)

    if check_for_win():
        show_end_screen(win_screen)
        return

    turn += 1
    update_turn_text()

    do_computer_turn()
    if check_for_win():
        show_end_screen(lose_screen)
        return

    if board_is_full():
        show_end_screen(tie_screen)

@when("click", ".end-button")
def restart_button_click():
    window.location.reload()

def take_slot(slot, mark):
    """Write a mark into a slot and colour it to match its owner."""
    slot.textContent = mark
    slot.classList.add("player" if mark == PLAYER else "computer")

def update_turn_text():
    """Refresh the turn counter, naming the current player in friend mode."""
    if game_mode == "friend":
        turnText.textContent = f"Turn: #{turn} \u00b7 {current_mark}"
    else:
        turnText.textContent = f"Turn: #{turn}"

def show_end_screen(screen, title=None, message=None):
    """Play the game over sound and reveal an end screen, optionally retitled."""
    if title:
        screen.querySelector(".end-title").textContent = title
    if message:
        screen.querySelector(".end-message").textContent = message

    play_sound(game_over_sfx)
    screen.classList.add("visible")

def do_computer_turn():
    """Make the computer's move & update the grid."""
    where_to_move = get_computer_move()

    if where_to_move is None:
        return  # board is full, nothing to do

    take_slot(grid[where_to_move], COMPUTER)

def read_board():
    """Read the current marks off the grid as a list of 9 strings ('' = empty)."""
    return [grid[i].textContent.strip() for i in range(9)]

def board_is_full():
    """True once every slot has a mark in it."""
    return all(read_board())

def find_line_completion(board, mark):
    """
    Find a slot that completes a line for `mark`.

    Looks for any line already holding two of `mark` plus one empty slot,
    and returns the index of that empty slot. Returns None if there is none.
    """
    for line in WIN_LINES:
        marks = [board[i] for i in line]

        if marks.count(mark) == 2 and marks.count("") == 1:
            # the one empty slot in this line is the completing move
            for i in line:
                if not board[i]:
                    return i

    return None

def get_computer_move():
    """
    Using advanced reasoning & thoroughly analyzing the board, the computer
    chooses what slot to move, thinking of how the user could win, how it could win,
    and involving randomness if no threats or opportunites.
    """
    board = read_board()

    # 1. opportunity: if the computer can win right now, take it
    winning_move = find_line_completion(board, COMPUTER)
    if winning_move is not None:
        print(f"computer wins at {winning_move}")
        return winning_move

    # 2. threat: otherwise stop the player from winning next turn
    blocking_move = find_line_completion(board, PLAYER)
    if blocking_move is not None:
        print(f"computer blocks at {blocking_move}")
        return blocking_move

    # 3. no threats or opportunities, so pick an empty slot at random
    empty_slots = [i for i, mark in enumerate(board) if not mark]
    if not empty_slots:
        return None

    choice = random.choice(empty_slots)
    print(f"computer picks {choice} at random")
    return choice

def check_for_win():
    """
    Analyes the board to see if there is a winner, and if there is, returns
    that winner's mark ("O" or "X"). Returns None when nobody has won.
    """
    board = read_board()

    for a, b, c in WIN_LINES:
        mark = board[a]

        if mark and mark == board[b] == board[c]:
            return mark

    return None
