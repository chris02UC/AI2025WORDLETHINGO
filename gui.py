import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import random
import io
import contextlib
import re
import threading
import time

import main as gameEngine

COLOR_BG = "#FFFFFF"
COLOR_DEFAULT = "#D3D6DA"
COLOR_GRAY = "#787C7E"
COLOR_YELLOW = "#C9B458"
COLOR_GREEN = "#6AAA64"
COLOR_WHITE = "#FFFFFF"
COLOR_BLACK = "#000000"

TITLE_FONT = ("Helvetica", 18, "bold")
GRID_FONT = ("Helvetica", 20, "bold")
STATUS_FONT = ("Helvetica", 12)

class WordleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wordle AI Suite")
        self.root.geometry("850x600")

        try:
            gameEngine._initialize_word_lists()
            self.permanent_answers = gameEngine.permanent_answers[:]
            self.all_allowed_words = list(set(gameEngine.wordsAllowed + self.permanent_answers))
            if not self.permanent_answers or not self.all_allowed_words:
                raise FileNotFoundError
        except FileNotFoundError:
            messagebox.showerror("Error", "Could not find 'words.txt' or 'wordsAllowed.txt'.\nMake sure they are in the same directory as gui.py.")
            self.root.destroy()
            return
            
        self.notebook = ttk.Notebook(root)
        
        self.mode1_tab = Mode1Tab(self.notebook, self)
        self.mode2_tab = Mode2Tab(self.notebook, self)
        self.mode3_tab = Mode3Tab(self.notebook, self)
        self.mode4_tab = Mode4Tab(self.notebook, self)
        self.mode5_tab = Mode5Tab(self.notebook, self)
        
        self.notebook.add(self.mode1_tab, text="Mode 1: AI vs. Random")
        self.notebook.add(self.mode2_tab, text="Mode 2: AI vs. Specific")
        self.notebook.add(self.mode3_tab, text="Mode 3: Human vs. AI")
        self.notebook.add(self.mode4_tab, text="Mode 4: AI Helper")
        self.notebook.add(self.mode5_tab, text="Mode 5: Full Simulation")
        
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

def create_grid(parent_frame):
    grid_labels = []
    for r in range(6):
        row_labels = []
        for c in range(5):
            label = tk.Label(parent_frame, text="", width=4, height=2, 
                             bg=COLOR_DEFAULT, relief="solid", borderwidth=1,
                             font=GRID_FONT, fg=COLOR_BLACK)
            label.grid(row=r, column=c, padx=2, pady=2)
            row_labels.append(label)
        grid_labels.append(row_labels)
    return grid_labels

def update_grid_row(grid_labels, row, guess, colors_str):
    color_map = {'G': COLOR_GREEN, 'Y': COLOR_YELLOW, 'B': COLOR_GRAY}
    for i in range(5):
        char = guess[i].upper()
        color_char = colors_str[i]
        bg_color = color_map.get(color_char, COLOR_DEFAULT)
        
        label = grid_labels[row][i]
        label.config(text=char, bg=bg_color, fg=COLOR_WHITE)

def clear_grid(grid_labels):
    for r in range(6):
        for c in range(5):
            grid_labels[r][c].config(text="", bg=COLOR_DEFAULT, fg=COLOR_BLACK)


class ScrollableTab(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.canvas = tk.Canvas(self, borderwidth=0, background=COLOR_BG)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        style = ttk.Style()
        style.configure("Scrollable.TFrame", background=COLOR_BG)
        self.scrollable_frame.configure(style="Scrollable.TFrame")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event=None):
        self.canvas.itemconfig(self.canvas_window, width=event.width)


class TextOutputTab(ScrollableTab):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.output_text = None
        self.thread = None

    def create_text_output(self):
        self.output_text = scrolledtext.ScrolledText(self.scrollable_frame, wrap=tk.WORD, font=("Courier New", 10))
        self.output_text.pack(expand=True, fill='both', padx=10, pady=10)
        self.output_text.config(state=tk.DISABLED)
        self.output_text.bind("<<ThreadDone>>", self.on_thread_done)

    def run_function_in_thread(self, target_function, *args):
        """Runs a function in a thread and displays its output."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert(tk.END, "Running... This may take a moment.\n")
        self.output_text.config(state=tk.DISABLED)
        
        self.thread = threading.Thread(target=self._thread_wrapper, args=(target_function, *args))
        self.thread.daemon = True
        self.thread.start()

    def _thread_wrapper(self, target_function, *args):
        """Internal wrapper to capture stdout from the threaded function."""
        f = io.StringIO()
        try:
            with contextlib.redirect_stdout(f):
                target_function(*args)
            self.output = f.getvalue()
        except Exception as e:
            self.output = f"An error occurred: {e}\n\nCheck console for details."
            print(e)
        
        self.output_text.event_generate("<<ThreadDone>>")

    def on_thread_done(self, event=None):
        """Updates the text box when the thread finishes."""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete('1.0', tk.END)
        self.output_text.insert(tk.END, self.output)
        self.output_text.config(state=tk.DISABLED)


class AIGameTab(ScrollableTab):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.control_frame = ttk.Frame(self.scrollable_frame)
        self.control_frame.pack(fill='x', padx=10, pady=10)
        
        self.grid_frame = ttk.Frame(self.scrollable_frame)
        self.grid_frame.pack(pady=10)
        
        self.ai_grid_labels = create_grid(self.grid_frame)
        
        self.status_label = ttk.Label(self.scrollable_frame, text="Start a game to begin.", font=STATUS_FONT)
        self.status_label.pack(pady=10)
        
        self.next_step_button = ttk.Button(self.scrollable_frame, text="Next Step", command=self.run_ai_step, state=tk.DISABLED)
        self.next_step_button.pack(pady=5)
        
        self.game_over = True
        self.target_word = ""
        self.ai_row = 0
        self.ai_available_words = []
        self.ai_guesses = []

    def start_game_logic(self, target_word):
        if not target_word or target_word not in self.app.permanent_answers:
            messagebox.showerror("Word Error", f"'{target_word}' is not a valid 5-letter answer word.")
            return False
            
        self.game_over = False
        self.target_word = target_word
        self.ai_row = 0
        self.ai_guesses = []
        self.ai_available_words = self.app.permanent_answers[:]
        
        clear_grid(self.ai_grid_labels)
        self.status_label.config(text=f"Target word set. Press 'Next Step' for AI's first guess.")
        self.next_step_button.config(state=tk.NORMAL)
        return True

    def run_ai_step(self):
        if self.game_over:
            return

        if self.ai_row == 0:
            ai_guess = "salet"
        else:
            if not self.ai_available_words:
                self.status_label.config(text="Error: AI has no possible words left.")
                self.end_game()
                return
                
            last_ai_guess = self.ai_guesses[-1]
            self.ai_available_words = gameEngine.filter_words(
                self.ai_available_words, last_ai_guess, self.target_word
            )
            
            if not self.ai_available_words:
                self.status_label.config(text="Error: AI has no possible words left after filtering.")
                self.end_game()
                return
            elif len(self.ai_available_words) == 1:
                ai_guess = self.ai_available_words[0]
            elif gameEngine.isBlimp(self.ai_available_words):
                self.status_label.config(text="AI: Blimp condition detected. Finding filter word...")
                ai_guess = gameEngine.blimpSearch(self.ai_available_words)
            else:
                self.status_label.config(text="AI: Finding best word by frequency...")
                ai_guess = gameEngine.getMaxValue1(self.ai_available_words)
        
        self.ai_guesses.append(ai_guess)
        colors_str = gameEngine.get_guess_colors(ai_guess, self.target_word)
        
        update_grid_row(self.ai_grid_labels, self.ai_row, ai_guess, colors_str)
        self.ai_row += 1

        if ai_guess == self.target_word:
            self.status_label.config(text=f"AI solved it in {self.ai_row} steps!")
            self.end_game()
            return

        if self.ai_row == 6:
            self.status_label.config(text=f"AI failed! The word was {self.target_word.upper()}")
            self.end_game()
            return
            
        self.status_label.config(text=f"AI guessed '{ai_guess}'. Press 'Next Step'.")

    def end_game(self):
        self.game_over = True
        self.next_step_button.config(state=tk.DISABLED)

class Mode1Tab(AIGameTab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        
        self.start_button = ttk.Button(self.control_frame, text="Start New Random Game", command=self.start_random_game)
        self.start_button.pack()

    def start_random_game(self):
        target = random.choice(self.app.permanent_answers)
        self.start_game_logic(target)
        self.status_label.config(text="New random word selected. Press 'Next Step'.")

class Mode2Tab(AIGameTab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        
        ttk.Label(self.control_frame, text="Target Word:").pack(side=tk.LEFT, padx=5)
        self.word_entry = ttk.Entry(self.control_frame, width=10)
        self.word_entry.pack(side=tk.LEFT, padx=5)
        
        self.start_button = ttk.Button(self.control_frame, text="Start Game", command=self.start_specific_game)
        self.start_button.pack(side=tk.LEFT, padx=5)

    def start_specific_game(self):
        target = self.word_entry.get().lower().strip()
        if self.start_game_logic(target):
            self.word_entry.config(state=tk.DISABLED)
            self.start_button.config(state=tk.DISABLED)
            
    def end_game(self):
        super().end_game()
        self.word_entry.config(state=tk.NORMAL)
        self.start_button.config(state=tk.NORMAL)


class Mode3Tab(ScrollableTab):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.timer_job = None
        
        self.title_label = tk.Label(self.scrollable_frame, text="HUMAN vs. AI", font=TITLE_FONT, bg=COLOR_BG, fg=COLOR_BLACK)
        self.title_label.pack(pady=10)

        self.game_frame = tk.Frame(self.scrollable_frame, bg=COLOR_BG)
        self.game_frame.pack(pady=10)

        self.human_frame = tk.Frame(self.game_frame, bg=COLOR_BG, padx=10)
        self.human_frame.pack(side=tk.LEFT)
        tk.Label(self.human_frame, text="Your Guesses", font=STATUS_FONT, bg=COLOR_BG).pack()
        self.human_grid_frame = tk.Frame(self.human_frame, bg=COLOR_BG)
        self.human_grid_frame.pack(pady=5)

        self.ai_frame = tk.Frame(self.game_frame, bg=COLOR_BG, padx=10)
        self.ai_frame.pack(side=tk.LEFT)
        tk.Label(self.ai_frame, text="AI's Guesses", font=STATUS_FONT, bg=COLOR_BG).pack()
        self.ai_grid_frame = tk.Frame(self.ai_frame, bg=COLOR_BG)
        self.ai_grid_frame.pack(pady=5)

        self.human_grid_labels = create_grid(self.human_grid_frame)
        self.ai_grid_labels = create_grid(self.ai_grid_frame)

        self.input_frame = tk.Frame(self.scrollable_frame, bg=COLOR_BG)
        self.input_frame.pack(pady=10)

        self.difficulty_frame = tk.Frame(self.scrollable_frame, bg=COLOR_BG)
        self.difficulty_frame.pack(pady=5)
        
        tk.Label(self.difficulty_frame, text="AI Difficulty:", font=STATUS_FONT, bg=COLOR_BG).pack(side=tk.LEFT, padx=5)
        
        self.difficulty_var = tk.StringVar(value="Hard")
        self.difficulty_selector = ttk.Combobox(
            self.difficulty_frame, 
            textvariable=self.difficulty_var,
            values=["Easy", "Medium", "Hard"],
            state="readonly",
            width=10
        )
        self.difficulty_selector.pack(side=tk.LEFT, padx=5)

        self.vision_frame = tk.Frame(self.scrollable_frame, bg=COLOR_BG)
        self.vision_frame.pack(pady=5)
        
        tk.Label(self.vision_frame, text="Player Vision:", font=STATUS_FONT, bg=COLOR_BG).pack(side=tk.LEFT, padx=5)
        
        self.vision_var = tk.StringVar(value="Full Vision")
        self.vision_selector = ttk.Combobox(
            self.vision_frame, 
            textvariable=self.vision_var,
            values=["Full Vision", "Half Blind", "Blind"],
            state="readonly",
            width=10
        )
        self.vision_selector.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(self.scrollable_frame, text="", font=STATUS_FONT, bg=COLOR_BG, fg=COLOR_BLACK)

        tk.Label(self.input_frame, text="Enter Guess:", font=STATUS_FONT, bg=COLOR_BG).pack(side=tk.LEFT, padx=5)
        self.guess_entry = tk.Entry(self.input_frame, width=7, font=GRID_FONT, justify='center')
        self.guess_entry.pack(side=tk.LEFT, padx=5)
        self.guess_entry.bind("<Return>", self.on_human_guess)
        
        self.status_label = tk.Label(self.scrollable_frame, text="", font=STATUS_FONT, bg=COLOR_BG, fg=COLOR_BLACK)
        self.status_label.pack(pady=5)
        
        self.timer_frame = ttk.Frame(self.scrollable_frame)
        self.timer_frame.pack(pady=5)
        
        ttk.Label(self.timer_frame, text="Turn Timer (sec):", font=STATUS_FONT).pack(side=tk.LEFT, padx=5)
        self.timer_spinbox = ttk.Spinbox(self.timer_frame, from_=0, to=120, width=4, font=STATUS_FONT)
        self.timer_spinbox.set(0)
        self.timer_spinbox.pack(side=tk.LEFT, padx=5)
        
        self.timer_label = ttk.Label(self.timer_frame, text="", font=(STATUS_FONT[0], STATUS_FONT[1], "bold"), foreground="red")
        self.timer_label.pack(side=tk.LEFT, padx=10)

        self.reset_button = ttk.Button(self.scrollable_frame, text="New Game", command=self.start_new_game)
        self.reset_button.pack(pady=10)

        self.start_new_game()

    def start_turn_timer(self):
        self.stop_turn_timer() 
        try:
            self.seconds_left = int(self.timer_spinbox.get())
        except ValueError:
            self.seconds_left = 0
            
        if self.seconds_left > 0:
            self.timer_label.config(text=f"Time: {self.seconds_left}")
            self.timer_spinbox.config(state=tk.DISABLED) 
            self.countdown()
        else:
            self.timer_label.config(text="")
            self.timer_spinbox.config(state=tk.NORMAL) 

    def stop_turn_timer(self):
        if self.timer_job:
            self.app.root.after_cancel(self.timer_job)
            self.timer_job = None
        self.timer_label.config(text="")
        self.timer_spinbox.config(state=tk.NORMAL) 

    def countdown(self):
        if self.game_over:
            return
            
        self.seconds_left -= 1
        self.timer_label.config(text=f"Time: {self.seconds_left}")
        
        if self.seconds_left <= 0:
            self.timer_label.config(text="Time's Up!")
            self.end_game(f"Time's up! The word was: {self.target_word.upper()}")
        else:
            self.timer_job = self.app.root.after(1000, self.countdown)

    def start_new_game(self):
        self.stop_turn_timer()
        self.game_over = False
        self.target_word = random.choice(self.app.permanent_answers)

        self.human_row = 0
        self.ai_row = 0
        self.ai_guesses = []
        self.ai_available_words = self.app.permanent_answers[:]
        
        clear_grid(self.human_grid_labels)
        clear_grid(self.ai_grid_labels)
        
        self.status_label.config(text="Game started. Enter your first guess.")
        self.guess_entry.config(state=tk.NORMAL)
        self.guess_entry.delete(0, tk.END)
        self.guess_entry.focus()
        self.difficulty_selector.config(state="readonly")
        self.vision_selector.config(state="readonly")
        self.start_turn_timer()

    def on_human_guess(self, event=None):
        if self.game_over:
            return

        if self.human_row == 0:
            self.difficulty_selector.config(state=tk.DISABLED)
            self.vision_selector.config(state=tk.DISABLED)

        guess = self.guess_entry.get().lower().strip()
        self.guess_entry.delete(0, tk.END)

        if len(guess) != 5:
            self.status_label.config(text="Guess must be 5 letters.")
            return
        if guess not in self.app.all_allowed_words:
            self.status_label.config(text=f"'{guess}' is not in the word list.")
            return

        # Valid guess, so stop the timer
        self.stop_turn_timer()

        colors_str = gameEngine.get_guess_colors(guess, self.target_word)
        update_grid_row(self.human_grid_labels, self.human_row, guess, colors_str)
        self.human_row += 1

        if guess == self.target_word:
            self.end_game("Congratulations, you win! 🎉")
            return
        
        if self.human_row == 6:
            self.end_game(f"You lose. The word was: {self.target_word.upper()}")
            return

        self.status_label.config(text="AI is thinking...")
        self.guess_entry.config(state=tk.DISABLED)
        
        self.app.root.update_idletasks() 
        self.app.root.after(500, self.run_ai_turn) 

    def run_ai_turn(self):
        difficulty = self.difficulty_var.get()
        vision = self.vision_var.get()
        
        if self.ai_row == 0:
            if difficulty == "Easy":
                ai_guess = random.choice(self.ai_available_words)
            else:
                ai_guess = "salet"
        else:
            last_ai_guess = self.ai_guesses[-1]
            self.ai_available_words = gameEngine.filter_words(
                self.ai_available_words, last_ai_guess, self.target_word
            )
            
            if not self.ai_available_words:
                ai_guess = "salet"
            elif len(self.ai_available_words) == 1:
                ai_guess = self.ai_available_words[0]
            
            elif difficulty == "Hard":
                if gameEngine.isBlimp(self.ai_available_words):
                    ai_guess = gameEngine.blimpSearch(self.ai_available_words)
                else:
                    ai_guess = gameEngine.getMaxValue1(self.ai_available_words)
            else:
                ai_guess = random.choice(self.ai_available_words)
        
        self.ai_guesses.append(ai_guess)
        ai_colors_str = gameEngine.get_guess_colors(ai_guess, self.target_word)
        
        if vision == "Full Vision":
            update_grid_row(self.ai_grid_labels, self.ai_row, ai_guess, ai_colors_str)
        elif vision == "Half Blind":
            all_gray_colors = "B" * 5
            update_grid_row(self.ai_grid_labels, self.ai_row, ai_guess, all_gray_colors)
        elif vision == "Blind":
            pass

        self.ai_row += 1

        if ai_guess == self.target_word:
            self.end_game(f"AI wins. The word was: {self.target_word.upper()}")
            return

        self.status_label.config(text="Your turn.")
        self.guess_entry.config(state=tk.NORMAL)
        self.guess_entry.focus()
        self.start_turn_timer()

    def end_game(self, message):
        self.stop_turn_timer()
        self.game_over = True
        
        if self.vision_var.get() == "Blind" and self.ai_row > 0:
            self.status_label.config(text=f"{message} Revealing AI grid...")
            for i, guess in enumerate(self.ai_guesses):
                colors_str = gameEngine.get_guess_colors(guess, self.target_word)
                update_grid_row(self.ai_grid_labels, i, guess, colors_str)
        else:
            self.status_label.config(text=message)
            
        self.guess_entry.config(state=tk.DISABLED)
        
        self.difficulty_selector.config(state="readonly")
        self.vision_selector.config(state="readonly")
        self.timer_spinbox.config(state=tk.NORMAL)


class Mode4Tab(ScrollableTab):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.grid_frame = ttk.Frame(self.scrollable_frame)
        self.grid_frame.pack(pady=10)
        
        self.helper_grid_labels = create_grid(self.grid_frame)
        self.tile_feedback = []
        
        self.status_label = ttk.Label(self.scrollable_frame, text="", font=STATUS_FONT)
        self.status_label.pack(pady=10)
        
        self.control_frame = ttk.Frame(self.scrollable_frame)
        self.control_frame.pack(pady=5)

        self.submit_button = ttk.Button(self.control_frame, text="Submit Feedback", command=self.submit_feedback, state=tk.DISABLED)
        self.submit_button.pack(side=tk.LEFT, padx=10)

        self.reset_button = ttk.Button(self.control_frame, text="New Game", command=self.start_new_helper)
        self.reset_button.pack(side=tk.LEFT, padx=10)
        
        self.list_frame = ttk.LabelFrame(self.scrollable_frame, text="Possible Words", padding=10)
        self.list_frame.pack(expand=True, fill='both', padx=10, pady=10)
        
        self.word_list_text = scrolledtext.ScrolledText(self.list_frame, wrap=tk.WORD, font=("Courier New", 10))
        self.word_list_text.pack(expand=True, fill='both')
        
        self.start_new_helper()

    def start_new_helper(self):
        self.game_over = False
        self.turn = 0
        self.ai_guess = "salet"
        self.ai_available_words = self.app.permanent_answers[:]
        
        clear_grid(self.helper_grid_labels)
        self.update_list_text(f"{len(self.ai_available_words)} words remaining.")
        
        self.display_ai_guess()
        self.submit_button.config(state=tk.NORMAL)

    def display_ai_guess(self):
        if self.game_over: return
        
        self.status_label.config(text=f"AI Suggests: {self.ai_guess.upper()}. Click tiles to set colors.")
        
        for c in range(5):
            label = self.helper_grid_labels[self.turn][c]
            label.config(text=self.ai_guess[c].upper(), bg=COLOR_GRAY, fg=COLOR_WHITE)
            label.bind("<Button-1>", lambda e, r=self.turn, col=c: self.on_tile_click(r, col))
        
        self.reset_row_feedback()

    def on_tile_click(self, row, col):
        if self.game_over or row != self.turn:
            return

        label = self.helper_grid_labels[row][col]
        current_color_char = self.tile_feedback[col]
        
        if current_color_char == 'B':
            new_color_char = 'Y'
            bg_color = COLOR_YELLOW
            fg_color = COLOR_WHITE
        elif current_color_char == 'Y':
            new_color_char = 'G'
            bg_color = COLOR_GREEN
            fg_color = COLOR_WHITE
        else:
            new_color_char = 'B'
            bg_color = COLOR_GRAY
            fg_color = COLOR_WHITE
            
        self.tile_feedback[col] = new_color_char
        label.config(bg=bg_color, fg=fg_color)

    def submit_feedback(self):
        if self.game_over: return
        
        feedback_byg = "".join(self.tile_feedback)
        
        if feedback_byg.count('B') == 5:
             if not messagebox.askyesno("Submit Feedback?", "You have marked all letters as Black (Gray). Is this correct?"):
                 return
        
        feedback_num = feedback_byg.replace('B', '0').replace('Y', '1').replace('G', '2')

        for c in range(5):
            self.helper_grid_labels[self.turn][c].unbind("<Button-1>")
            
        if feedback_byg == "GGGGG":
            self.status_label.config(text=f"Congratulations! Solved in {self.turn + 1} turns.")
            self.update_list_text("Solved!")
            self.end_helper_game()
            return
            
        self.turn += 1
        if self.turn == 6:
            self.status_label.config(text="Game over! Out of turns.")
            self.update_list_text(f"Game over. Remaining: {self.ai_available_words}")
            self.end_helper_game()
            return

        try:
            self.ai_available_words = gameEngine.gameFilter(self.ai_guess, feedback_num, self.ai_available_words)
            count = len(self.ai_available_words)
            
            if count == 0:
                self.status_label.config(text="Error: No words match that feedback.")
                self.update_list_text("No words found. Check your feedback.")
                self.end_helper_game()
                return
            
            if count <= 50:
                self.update_list_text(f"{count} words remaining:\n{', '.join(self.ai_available_words)}")
            else:
                self.update_list_text(f"{count} words remaining.")

            if count == 1:
                self.ai_guess = self.ai_available_words[0]
            elif gameEngine.isBlimp(self.ai_available_words):
                self.status_label.config(text="Blimp condition detected. Finding filter word...")
                self.ai_guess = gameEngine.blimpSearch(self.ai_available_words)
            else:
                self.ai_guess = gameEngine.getMaxValue1(self.ai_available_words)
                
            self.display_ai_guess()

        except Exception as e:
            self.status_label.config(text=f"An error occurred: {e}")
            self.end_helper_game()

    def end_helper_game(self):
        self.game_over = True
        self.submit_button.config(state=tk.DISABLED)
        if self.turn < 6:
            for c in range(5):
                self.helper_grid_labels[self.turn][c].unbind("<Button-1>")

    def reset_row_feedback(self):
        self.tile_feedback = ['B'] * 5 
        
    def update_list_text(self, message):
        self.word_list_text.config(state=tk.NORMAL)
        self.word_list_text.delete('1.0', tk.END)
        self.word_list_text.insert(tk.END, message)
        self.word_list_text.config(state=tk.DISABLED)

class Mode5Tab(TextOutputTab):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        
        top_frame = ttk.Frame(self.scrollable_frame)
        top_frame.pack(fill='x', padx=10, pady=10)
        
        self.run_button = ttk.Button(top_frame, text="Run Full Simulation & Plot", command=self.run_sim)
        self.run_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(top_frame, text="WARNING: This takes several minutes.", foreground="red").pack(side=tk.LEFT, padx=10)
        
        self.create_text_output()
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, "Click the button to run the full simulation against all 2,315 answer words.\n")
        self.output_text.insert(tk.END, "This runs in a separate thread, so the GUI will NOT freeze.\n")
        self.output_text.insert(tk.END, "A Matplotlib window will pop up with the histogram when complete.")
        self.output_text.config(state=tk.DISABLED)

    def run_sim(self):
        if not gameEngine.MATPLOTLIB_AVAILABLE:
            messagebox.showerror("Error", "Matplotlib or NumPy not found. Cannot run Mode 5.")
            return

        self.run_button.config(state=tk.DISABLED, text="Running...")
        self.run_function_in_thread(gameEngine.run_full_simulation_and_plot)
        self.output_text.bind("<<ThreadDone>>", self.on_thread_done_mode5)

    def on_thread_done_mode5(self, event=None):
        self.on_thread_done()
        self.run_button.config(state=tk.NORMAL, text="Run Full Simulation & Plot")


if __name__ == "__main__":
    root = tk.Tk()
    
    style = ttk.Style(root)
    style.configure("Scrollable.TFrame", background=COLOR_BG)

    app = WordleApp(root)
    root.mainloop()
