import random
import threading
import math
import re
import time

# packages for Mode 5
try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib or numpy not found. Mode 5 (Full Simulation) will not be able to plot.")

GRAY = "⬛"
YELLOW = "🟨"
GREEN = "🟩"

# --- Global Word Lists ---
try:
    GLOBAL_PERMANENT_ANSWERS = [i[:-1] for i in open("words.txt", "r").readlines()]
    GLOBAL_WORDS_ALLOWED = [i[:-1] for i in open("wordsAllowed.txt", "r").readlines()]
except FileNotFoundError:
    print("FATAL ERROR: words.txt or wordsAllowed.txt not found.")
    print("Please make sure the word list files are in the same directory as main.py")
    GLOBAL_PERMANENT_ANSWERS = []
    GLOBAL_WORDS_ALLOWED = []

available_words = []
permanent_answers = []
wordsAllowed = []

def _initialize_word_lists():
    """Resets the global game lists from the master lists."""
    global available_words, permanent_answers, wordsAllowed
    available_words = GLOBAL_PERMANENT_ANSWERS[:]
    permanent_answers = GLOBAL_PERMANENT_ANSWERS[:]
    wordsAllowed = GLOBAL_WORDS_ALLOWED[:]
    
    if not permanent_answers or not wordsAllowed:
        raise FileNotFoundError("Word lists could not be initialized. Check file paths.")
        

def get_letter_dictionary(word_list):   #gets a letter dictionary of the each letter and the number of times it appears in the word list
    letter_dictionary = {}
    for letter in "abcdefghijklmnopqrstuvwxyz":
        letter_dictionary.update({letter:0})
    for word in word_list:
        for letter in word:
            try:
                letter_dictionary.update({letter:(letter_dictionary[letter] + 1)})
            except KeyError:
                pass
    return letter_dictionary

def game_data_avg(game_data):   #returns average steps to complete a game
    try:
        total_steps = (game_data["1"] + 2 * game_data["2"] + 3 * game_data["3"] + 4 * game_data["4"] + 5 * game_data["5"] + 6 * game_data["6"])
        total_games = (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"])
        if total_games == 0:
            return 0
        return total_steps / total_games
    except:
        return 0

def repetition_filter(char, num_repetitions, wordList, exact):  #filters out words with incorrect number of character repetitions
    return_list = []
    if exact:
        for word in wordList:
            if word.count(char) == num_repetitions:
                return_list.append(word)
    else:
        for word in wordList:
            if word.count(char) >= num_repetitions:
                return_list.append(word)
    return return_list

def filter_words(return_list, guess, answer):   #returns a list of possible words left, given a guess and an answer
    current_list = return_list[:]
    colors = get_guess_colors(guess, answer)
    
    exact_counts = {}
    min_counts = {}
    
    for i in range(5):
        char = guess[i]
        
        gy_count = 0
        for j in range(5):
            if guess[j] == char and colors[j] in ('G', 'Y'):
                gy_count += 1
        if gy_count > 0:
            min_counts[char] = max(min_counts.get(char, 0), gy_count)
            
        if colors[i] == 'B' and char in min_counts:
            exact_counts[char] = min_counts[char]
            
    temp_list = []
    for word in current_list:
        valid = True
        
        for i in range(5):
            char = guess[i]
            color = colors[i]
            
            if color == 'G':
                if word[i] != char:
                    valid = False
                    break
            elif color == 'Y':
                if word[i] == char or char not in word:
                    valid = False
                    break
            elif color == 'B':
                if char not in min_counts and char in word:
                    valid = False
                    break
                pass
        
        if not valid:
            continue
            
        for char, count in min_counts.items():
            if char in exact_counts:
                if word.count(char) != exact_counts[char]:
                    valid = False
                    break
            elif word.count(char) < count:
                valid = False
                break
                
        if valid:
            temp_list.append(word)
            
    return temp_list

def filter(filterChar, position="any", repetitions="any", wordList="none"):
    returnList = []
    if type(position) == int:
        if position < 0 or position > 4:
            raise RuntimeError("InvalidCharacterPosition")
    
    if wordList == "none":
        wordList = permanent_answers[:] 

    for word in wordList:
        if position != "any":
            if word[position] == filterChar:
                if word.count(filterChar) == repetitions or repetitions == "any":
                    returnList.append(word)
        elif repetitions != "any":
            if filterChar in word and word.count(filterChar) == repetitions:
                returnList.append(word)
        else:
            if filterChar in word:
                returnList.append(word)
    return returnList

def inverseFilter(filterChar, wordList="none"): 
    returnList = []
    if wordList == "none":
        wordList = permanent_answers[:]
        
    for word in wordList:
        if filterChar not in word:
            returnList.append(word)
    return returnList

def wrongPositionFilter(filterChar, index, wordList="none"):
    returnList = []
    if wordList == "none":
        wordList = permanent_answers[:]
        
    for word in wordList:
        if filterChar != word[index]:
            returnList.append(word)
    return returnList

def word_state_repetition_filter(word, wordState, word_list):
    repeatedChars = {i: word.count(i) for i in list(set(word)) if word.count(i) > 1}
    charRepetitions = {i: 0 for i in repeatedChars.keys()}
    for char in repeatedChars.keys():
        for i in range(5):
            if word[i] == char and wordState[i] != "0":
                repeatedChars[char] -= 1
                charRepetitions[char] += 1
    for char in repeatedChars.keys():
        word_list = repetition_filter(char, charRepetitions[char], word_list, repeatedChars[char] != 0)
    return word_list

def get_word_value(word, letter_dictionary, counted_word=""):
    value = 0
    counted_letters = [letter for letter in counted_word]
    for letter in word:
        if letter not in counted_letters:
            value += letter_dictionary[letter]
            counted_letters.append(letter)
    return value

def isBlimp(wordList):
    list_len = len(wordList)
    if list_len < 2 or list_len > 15:
        return False

    if list_len > 1:
        fixed_positions = 0
        first_word = wordList[0]
        for i in range(5):
            letter = first_word[i]
            is_fixed = True
            for word in wordList[1:]:
                if word[i] != letter:
                    is_fixed = False
                    break
            if is_fixed:
                fixed_positions += 1
        
        if fixed_positions >= 2:
            return True

    if list_len < 3:
        return False
        
    threshold = math.floor(list_len/2)
    commonLettersDict = {}
    for word1 in wordList:
        for word2 in wordList:
            if word2 == word1:
                continue
            shared_letters = list(set(word1) & set(word2))
            if len(shared_letters) >= 3: 
                commonLetters = ""
                for letter in shared_letters:
                    commonLetters += letter
                commonLetters = "".join(sorted(commonLetters))
                try:
                    commonLettersDict[commonLetters] += 1
                    if commonLettersDict[commonLetters] >= threshold:
                        return True
                except:
                    commonLettersDict[commonLetters] = 1
                    
    return False
    
def blimpSearch(wordList):
    global wordsAllowed
    best_guess = ""
    min_max_remaining_size = len(wordList) + 1
    avg_for_best = float(len(wordList) + 1)

    candidate_guesses = list(set(wordsAllowed + wordList))

    if not candidate_guesses:
        return getMaxValue1(wordList) 

    for candidate in candidate_guesses:
        max_remaining_size = 0
        possible_outcome_sizes = []
        
        for potential_answer in wordList:
            simulated_remaining_list = filter_words(wordList[:], candidate, potential_answer)
            outcome_size = len(simulated_remaining_list)
            possible_outcome_sizes.append(outcome_size)

            if outcome_size > max_remaining_size:
                max_remaining_size = outcome_size
            
            if max_remaining_size > min_max_remaining_size:
                break
        
        if max_remaining_size > min_max_remaining_size:
            continue

        current_avg = sum(possible_outcome_sizes) / len(possible_outcome_sizes)

        if max_remaining_size < min_max_remaining_size:
            min_max_remaining_size = max_remaining_size
            avg_for_best = current_avg
            best_guess = candidate
            
        elif max_remaining_size == min_max_remaining_size:
            if current_avg < avg_for_best:
                avg_for_best = current_avg
                best_guess = candidate
            elif current_avg == avg_for_best:
                if (best_guess not in wordList) and (candidate in wordList):
                    best_guess = candidate

    if not best_guess:
        print("Warning: BlimpSearch fallback triggered.")
        return getMaxValue1(wordList) 

    return best_guess

def getMaxValue1(wordList): #returns highest word by letter frequency
    if not wordList:
        return "salet"
    letterDictionary = get_letter_dictionary(wordList)
    wordValues = {word:get_word_value(word, letterDictionary) for word in wordList}
    if not wordValues: 
        return wordList[0] 
    return max(wordValues, key=wordValues.get)

def gameFilter(word, wordState, word_list):   #filters words using game output information
    first_letter = int(wordState[0])
    second_letter = int(wordState[1])
    third_letter = int(wordState[2])
    fourth_letter = int(wordState[3])
    fifth_letter = int(wordState[4])
    lettersInWord = [word[i] for i in range(0, 5) if wordState[i] == "1" or wordState[i] == "2"]
    if first_letter == 0:
        if word[0] not in lettersInWord:
            word_list = inverseFilter(word[0], word_list)
    elif first_letter == 1:
        word_list = filter(word[0], wordList=word_list)
        word_list = wrongPositionFilter(word[0], 0, word_list)
    elif first_letter == 2:
        word_list = filter(word[0], position=0, wordList=word_list)
    if second_letter == 0:
        if word[1] not in lettersInWord:
            word_list = inverseFilter(word[1], word_list)
    elif second_letter == 1:
        word_list = filter(word[1], wordList=word_list)
        word_list = wrongPositionFilter(word[1], 1, word_list)
    elif second_letter == 2:
        word_list = filter(word[1], position=1, wordList=word_list)
    if third_letter == 0:
        if word[2] not in lettersInWord:
            word_list = inverseFilter(word[2], word_list)
    elif third_letter == 1:
        word_list = filter(word[2], wordList=word_list)
        word_list = wrongPositionFilter(word[2], 2, word_list)
    elif third_letter == 2:
        word_list = filter(word[2], position=2, wordList=word_list)
    if fourth_letter == 0:
        if word[3] not in lettersInWord:
            word_list = inverseFilter(word[3], word_list)
    elif fourth_letter == 1:
        word_list = filter(word[3], wordList=word_list)
        word_list = wrongPositionFilter(word[3], 3, word_list)
    elif fourth_letter == 2:
        word_list = filter(word[3], position=3, wordList=word_list)
    if fifth_letter == 0:
        if word[4] not in lettersInWord:
            word_list = inverseFilter(word[4], word_list)
    elif fifth_letter == 1:
        word_list = filter(word[4], wordList=word_list)
        word_list = wrongPositionFilter(word[4], 4, word_list)
    elif fifth_letter == 2:
        word_list = filter(word[4], position=4, wordList=word_list)
    if len(set(list(word))) != len(word):
        word_list = word_state_repetition_filter(word, wordState, word_list)
    return word_list

def get_guess_colors(guess, target_word):
    if len(guess) != 5 or len(target_word) != 5:
        return "Error"

    colors = [''] * 5
    target_list = list(target_word) 

    for i in range(5):
        if guess[i] == target_list[i]:
            colors[i] = 'G'
            target_list[i] = None 

    for i in range(5):
        if colors[i] == '':
            if guess[i] in target_list:
                colors[i] = 'Y'
                target_list[target_list.index(guess[i])] = None
            else:
                colors[i] = 'B'

    return "".join(colors) 

def format_colors_to_emoji(color_string):
    emoji_map = {'B': GRAY, 'G': GREEN, 'Y': YELLOW}
    return "".join(emoji_map.get(char, char) for char in color_string)


# --- MODE 1: AI vs. Random Word ---

def run_ai_simulation(n):
    print(f"\n--- Starting AI Simulation ({n} games) ---")
    game_data = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "DNF": 0}

    try:
        _initialize_word_lists()
    except FileNotFoundError as e:
        print(e)
        return

    global available_words, permanent_answers, wordsAllowed # Use the lists initialized
    
    for i in range(n):
        print(f"\n--- Game {i+1} ---")
        current_available_words = permanent_answers[:] 
        test_word = random.choice(permanent_answers)
        print(f"Target Word: {test_word}")
        guess_history = []
        steps = 0

        # --- First Guess ---
        guessWord = "salet"
        steps = 1
        guess_history.append(guessWord)
        colors = get_guess_colors(guessWord, test_word)
        emoji_output = format_colors_to_emoji(colors)
        print(f"Guess {steps}: {guessWord} -> {emoji_output}")

        if guessWord == test_word:
            print(f"Solved in {steps} steps!")
            game_data.update({str(steps): game_data[str(steps)] + 1})
            continue 

        current_available_words = filter_words(current_available_words, guessWord, test_word)
        print(f"  Remaining possible words: {len(current_available_words)}")
        if test_word not in current_available_words and len(current_available_words) > 0:
             print(f"  ***Warning: Target word '{test_word}' was filtered out!***")

        # --- Subsequent Guesses ---
        solved = False
        for j in range(5): 
            if not current_available_words:
                print("  ***Error: No possible words left!***")
                steps = 7
                break

            if len(current_available_words) == 1:
                guessWord = current_available_words[0]
            elif isBlimp(current_available_words):
                 print("  (Blimp condition detected)")
                 guessWord = blimpSearch(current_available_words) 
            else:
                guessWord = getMaxValue1(current_available_words)

            steps += 1
            guess_history.append(guessWord)
            colors = get_guess_colors(guessWord, test_word)
            emoji_output = format_colors_to_emoji(colors)
            print(f"Guess {steps}: {guessWord} -> {emoji_output}")

            if guessWord == test_word:
                print(f"Solved in {steps} steps!")
                game_data.update({str(steps): game_data[str(steps)] + 1})
                solved = True
                break 

            current_available_words = filter_words(current_available_words, guessWord, test_word)
            print(f"  Remaining possible words: {len(current_available_words)}")
            if test_word not in current_available_words and len(current_available_words) > 0:
                print(f"  ***Warning: Target word '{test_word}' was filtered out!***")
            
            if len(current_available_words) == 1 and current_available_words[0] == test_word:
                steps += 1
                if steps > 6:
                    print("  (Would solve on step 7, marking as DNF)")
                    steps = 7 
                    break
                
                guessWord = current_available_words[0]
                guess_history.append(guessWord)
                colors = get_guess_colors(guessWord, test_word)
                emoji_output = format_colors_to_emoji(colors)
                print(f"Guess {steps}: {guessWord} -> {emoji_output}")
                print(f"Solved in {steps} steps!")
                game_data.update({str(steps): game_data[str(steps)] + 1})
                solved = True
                break

        if not solved:
             game_data.update({"DNF": game_data["DNF"] + 1})
             if steps < 6:
                print(f"Failed unexpectedly before 6 guesses (steps={steps}).")
             else:
                print(f"Failed to solve in 6 steps.")

        print(f"Guess History for game {i+1}: {guess_history}")
        if not solved:
            print(f"Remaining possibilities: {current_available_words}")

    print("\n--- Overall Results ---")
    total_games = sum(game_data.values())
    if total_games == 0:
        print("No games were simulated.")
        return
        
    success_count = total_games - game_data["DNF"]
    success_rate = (success_count / total_games)
    avg_steps = game_data_avg(game_data) 

    print(f"Method: highest_freq (with revised BlimpSearch)")
    print(f"Total Games Simulated: {total_games}")
    print(f"Results (Steps: Count): {game_data}")
    print(f"Success Rate: {success_rate * 100:.2f}%")
    print(f"Average Steps (for successful games): {avg_steps:.4f}")


# --- MODE 2: AI vs. User-Defined Word ---

def solve_specific_word(target_word):
    try:
        _initialize_word_lists()
    except FileNotFoundError as e:
        print(e)
        return
        
    global available_words, permanent_answers, wordsAllowed
    
    target_word = target_word.lower().strip()

    if len(target_word) != 5:
        print(f"Error: '{target_word}' is not 5 letters long.")
        return

    if target_word not in permanent_answers:
        print(f"Error: '{target_word}' is not in the list of possible answers (words.txt).")
        return

    # --- Simulation Logic ---
    current_available_words = permanent_answers[:]
    steps = 0
    guess_history = []

    print(f"Target Word: {target_word}")

    # --- First Guess ---
    guess = "salet"
    steps = 1
    guess_history.append(guess)
    colors = get_guess_colors(guess, target_word) 
    emoji_output = format_colors_to_emoji(colors)
    print(f"Guess {steps}: {guess} -> {emoji_output}")

    if guess == target_word:
        print(f"Solved in {steps} steps!")
        print(f"History: {guess_history}")
        return

    current_available_words = filter_words(current_available_words, guess, target_word)
    print(f"  Remaining possible words: {len(current_available_words)}")
    if target_word not in current_available_words and len(current_available_words) > 0:
         print(f"Warning: Target word '{target_word}' was filtered out! List: {current_available_words[:10]}")

    # --- Subsequent Guesses (Loop) ---
    for j in range(5):
        if not current_available_words:
             print("Error: No possible words left in list.")
             steps = -1 # Indicate failure state
             break

        if len(current_available_words) == 1:
            guess = current_available_words[0]
        elif isBlimp(current_available_words):
            print("  (Blimp condition detected)")
            guess = blimpSearch(current_available_words)
        else:
            guess = getMaxValue1(current_available_words)

        steps += 1
        guess_history.append(guess)
        colors = get_guess_colors(guess, target_word) 
        emoji_output = format_colors_to_emoji(colors)
        print(f"Guess {steps}: {guess} -> {emoji_output}")

        if guess == target_word:
            print(f"Solved in {steps} steps!")
            print(f"History: {guess_history}")
            return

        current_available_words = filter_words(current_available_words, guess, target_word)
        print(f"  Remaining possible words: {len(current_available_words)}")
        if target_word not in current_available_words and len(current_available_words) > 0:
            print(f"Warning: Target word '{target_word}' was filtered out! List: {current_available_words[:10]}")

    if steps != -1 and guess != target_word:
        print(f"Failed to solve in 6 steps.")
        print(f"History: {guess_history}")
        print(f"Remaining possibilities: {current_available_words}")


# --- MODE 3: Human VS AI Wordle ---

def play_human_vs_ai():
    try:
        _initialize_word_lists()
    except FileNotFoundError as e:
        print(e)
        return
        
    global available_words, permanent_answers, wordsAllowed
    
    while True:
        difficulty = input("Choose difficulty (easy/hard): ").lower().strip()
        if difficulty in ['easy', 'hard']:
            break
        else:
            print("Invalid input. Please type 'easy' or 'hard'.")

    target_word = random.choice(permanent_answers)
    print("\n--- Human vs AI Wordle ---")
    print(f"Difficulty: {difficulty.capitalize()}")
    # print(f"(DEBUG: The word is {target_word})")

    human_guesses_history = []
    ai_guesses_history = []
    ai_available_words = permanent_answers[:]

    # --- Game Loop ---
    for turn in range(1, 7):
        print(f"\n--- Turn {turn} ---")

        # --- Human Turn ---
        while True:
            human_guess = input(f"Your guess ({turn}/6): ").lower().strip()
            if len(human_guess) != 5:
                print("Guess must be 5 letters long.")
            elif human_guess not in wordsAllowed and human_guess not in permanent_answers:
                 print(f"'{human_guess}' is not in the list of allowed words.")
            else:
                break

        human_colors = get_guess_colors(human_guess, target_word)
        human_emoji = format_colors_to_emoji(human_colors)
        human_guesses_history.append(f"{human_guess} -> {human_emoji}")
        print(f"Your result: {human_emoji}")

        if human_guess == target_word:
            print(f"\nCongratulations! You guessed the word '{target_word}' in {turn} turns!")
            print("Human wins! 🎉")
            return

        # --- AI Turn ---
        print("AI is thinking...")
        if turn == 1:
            ai_guess = "salet"
        else:
            if ai_guesses_history:
                 last_ai_guess = ai_guesses_history[-1].split(" ")[0]
                 # Filter AI list based on its *own* last guess
                 ai_available_words = filter_words(ai_available_words[:], last_ai_guess, target_word)
                 # print(f"(AI Debug: Remaining words: {len(ai_available_words)})")

            if not ai_available_words:
                 print("AI Error: No possible words left for AI!")
                 ai_guess = "error" # Should not happen
            elif len(ai_available_words) == 1:
                 ai_guess = ai_available_words[0]
            elif isBlimp(ai_available_words):
                 print("(AI detected blimp condition)")
                 ai_guess = blimpSearch(ai_available_words)
            else:
                 ai_guess = getMaxValue1(ai_available_words)

        ai_colors = get_guess_colors(ai_guess, target_word)
        ai_emoji = format_colors_to_emoji(ai_colors)
        ai_guesses_history.append(f"{ai_guess} -> {ai_emoji}")

        if difficulty == 'easy':
            print(f"AI guess ({turn}/6): {ai_guess} -> {ai_emoji}")
        else:
            print(f"AI guess ({turn}/6): ????? -> {ai_emoji}") # Hide the word

        if ai_guess == target_word:
            print(f"\nThe AI guessed the word '{target_word}' in {turn} turns!")
            print("AI wins! 🤖")
            return 

    # --- No winner after 6 turns ---
    print("\n--- Game Over ---")
    print(f"Neither you nor the AI guessed the word in 6 turns.")
    print(f"The word was: {target_word}")
    print("\nYour Guesses:")
    for guess_info in human_guesses_history:
        print(guess_info)
    print("\nAI Guesses:")
    for guess_info in ai_guesses_history:
        print(guess_info)


# --- MODE 4: Wordle Helper AI ---

def play_ai_helper_mode():
    try:
        _initialize_word_lists()
    except FileNotFoundError as e:
        print(e)
        return
        
    global available_words, permanent_answers, wordsAllowed
    ai_available_words = permanent_answers[:]
    guess_history = []

    print("\n--- Wordle AI Helper ---")
    print("Instructions:")
    print("1. AI suggests a word.")
    print("2. Enter that word into your Wordle game.")
    print("3. Enter the 5-letter color result back here.")
    print("   Use 'B' for Black/Gray, 'Y' for Yellow, 'G' for Green (e.g., 'BGYBB').")

    # --- Game Loop ---
    for turn in range(1, 7):
        print(f"\n--- Turn {turn} ---")

        if turn == 1:
            ai_guess = "salet"
        else:
            if not ai_available_words:
                print("Error: No possible words left based on feedback!")
                return
            elif len(ai_available_words) == 1:
                ai_guess = ai_available_words[0] 
            elif isBlimp(ai_available_words):
                print("(AI detected blimp condition, choosing differentiating word...)")
                ai_guess = blimpSearch(ai_available_words)
            else:
                ai_guess = getMaxValue1(ai_available_words) 

        print(f"AI suggests guessing: {ai_guess.upper()}")

        color_feedback_byg = ""
        color_feedback_numeric = ""
        while True:
            color_feedback_byg = input("Enter the 5-letter color result (B/Y/G): ").upper().strip()
            if len(color_feedback_byg) == 5 and re.match("^[BGY]{5}$", color_feedback_byg):
                 # Convert BGY to 012 for gameFilter
                 color_feedback_numeric = color_feedback_byg.replace('B', '0').replace('Y', '1').replace('G', '2')
                 break
            else:
                 print("Invalid input. Please enter exactly 5 letters using only B, Y, or G.")

        emoji_feedback = format_colors_to_emoji(color_feedback_byg)
        guess_history.append(f"{ai_guess} -> {emoji_feedback}")

        if color_feedback_byg == "GGGGG":
            print(f"\nCongratulations! You found the word in {turn} turns!")
            print("History:")
            for entry in guess_history:
                print(entry)
            return # End game

        # --- AI Filters List ---
        # Note: This mode uses the older gameFilter logic.
        ai_available_words = gameFilter(ai_guess, color_feedback_numeric, ai_available_words)
        remaining_count = len(ai_available_words)

        print(f"Possible words remaining: {remaining_count}")
        if remaining_count <= 10 and remaining_count > 0:
             print(f"Possibilities: {', '.join(ai_available_words)}")
        elif remaining_count == 0:
             print("Uh oh! No words match the feedback provided. Double-check your color inputs.")
             return

    # --- End of Game ---
    print("\n--- Game Over ---")
    print("You've used all 6 turns.")
    if len(ai_available_words) == 1:
        print(f"The only remaining possibility was: {ai_available_words[0]}")
    elif len(ai_available_words) > 1 and len(ai_available_words) <= 10:
        print(f"The remaining possibilities were: {', '.join(ai_available_words)}")
    elif len(ai_available_words) > 10:
         print(f"There were still {len(ai_available_words)} possibilities left.")

    print("\nHistory:")
    for entry in guess_history:
        print(entry)


# --- MODE 5: Full Simulation & Histogram ---

def _solve_specific_word_for_stats(target_word, game_engine, initial_word_list):
    available_words = initial_word_list[:]
    steps = 0

    guess = "salet"
    steps = 1
    if guess == target_word:
        return steps
    available_words = game_engine.filter_words(available_words, guess, target_word)
    if target_word not in available_words and len(available_words) > 0:
         pass # print(f"Warning: Target {target_word} filtered out by {guess}")

    for j in range(5):
        if not available_words:
             return 7 # DNF

        if len(available_words) == 1:
            guess = available_words[0]
        elif game_engine.isBlimp(available_words):
            guess = game_engine.blimpSearch(available_words)
        else:
            guess = game_engine.getMaxValue1(available_words)

        steps += 1
        if guess == target_word:
            return steps

        available_words = game_engine.filter_words(available_words, guess, target_word)
        if target_word not in available_words and len(available_words) > 0:
            pass # print(f"Warning: Target {target_word} filtered out by {guess}")

    return 7 # DNF if loop finishes

def run_full_simulation_and_plot():
    if not MATPLOTLIB_AVAILABLE:
        print("\nError: Matplotlib and/or NumPy not installed.")
        print("Please install them (e.g., 'pip install matplotlib numpy') to run the full simulation.")
        return
        
    try:
        _initialize_word_lists()
    except FileNotFoundError as e:
        print(e)
        return
        
    global available_words, permanent_answers, wordsAllowed
    
    print("Starting full simulation for all words in words.txt...")
    print(f"This may take several minutes. ({len(permanent_answers)} words)")

    results = []
    dnf_words = [] 
    start_time = time.time()
    total_words = len(permanent_answers)

    for i, word in enumerate(permanent_answers):
        if (i+1) % 200 == 0:
            print(f"... processed {i+1}/{total_words} words ...")
        
        # Pass 'this' module as the game_engine
        steps = _solve_specific_word_for_stats(word, this_module, permanent_answers)
        results.append(steps)
        
        if steps == 7:
            dnf_words.append(word)
            
    end_time = time.time()
    print(f"\nSimulation complete. Processed {total_words} words in {end_time - start_time:.2f} seconds.")
    print("Generating histogram...")

    results_array = np.array(results)
    success_games = results_array[results_array <= 6]
    dnf_count = np.count_nonzero(results_array == 7)
    total_games = len(results_array)

    if total_games > 0:
        success_rate = len(success_games) / total_games
        avg_steps = np.mean(success_games) if len(success_games) > 0 else 0
        
        print(f"--- Overall Stats ---")
        print(f"Total Games: {total_games}")
        print(f"Success Rate: {success_rate * 100:.2f}%")
        print(f"Failed Games (DNF): {dnf_count}")
        print(f"Average Steps (on success): {avg_steps:.4f}")
        if dnf_count > 0: 
            print(f"Failed Words: {', '.join(dnf_words)}")
        print("\nDistribution of Guesses:")
        for i in range(1, 8):
            count = np.count_nonzero(results_array == i)
            label = f"DNF (7)" if i == 7 else f"{i} Steps"
            print(f"  {label}: {count} games")

    # Create the histogram
    bins = np.arange(1, 9)
    plt.figure(figsize=(10, 6))
    plt.hist(results_array, bins=bins, align='left', edgecolor='black', rwidth=0.8, color='skyblue')
    plt.title('Wordle Solver Performance (Highest Frequency Strategy)')
    plt.xlabel('Steps to Solve')
    plt.ylabel('Number of Games')
    tick_labels = [str(i) for i in range(1, 7)] + ['DNF (7+)']
    plt.xticks(ticks=np.arange(1, 8), labels=tick_labels)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    print("\nDisplaying plot...")
    plt.show()