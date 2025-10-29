import random
import threading
import math

GRAY = "⬛" # Represents Gray feedback
YELLOW = "🟨" # Represents Yellow feedback
GREEN = "🟩" # Represents Green feedback

available_words = [i[:-1] for i in open("words.txt", "r").readlines()]  #list of all possible answers
permanent_answers = [i[:-1] for i in open("words.txt", "r").readlines()]  #list of all possible answers, not changed in code
wordsAllowed = [i[:-1] for i in open("wordsAllowed.txt", "r").readlines()]  #list of all possible entries

def get_letter_dictionary(word_list):   #gets a letter dictionary of the each letter and the number of times it appears in the word list
    letter_dictionary = {}
    for letter in "abcdefghijklmnopqrstuvwxyz":
        letter_dictionary.update({letter:0})
    for word in word_list:
        for letter in word:
            letter_dictionary.update({letter:(letter_dictionary[letter] + 1)})
    return letter_dictionary

def game_data_avg(game_data):   #returns average steps to complete a game
    try:
        return (game_data["1"] + 2 * game_data["2"] + 3 * game_data["3"] + 4 * game_data["4"] + 5 * game_data["5"] + 6 * game_data["6"]) / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"])
    except:
        return 0

def repetition_filter(char, num_repetitions, wordList, exact):  #filters out words with incorrect number of character repetitions
    if exact:
        for word in wordList:
            if word.count(char) != num_repetitions:
                wordList.remove(word)
    else:
        for word in wordList:
            if word.count(char) < num_repetitions:
                wordList.remove(word)
    return wordList

def filter_words(return_list, guess, answer):   #returns a list of possible words left, given a guess and an answer
    for int in range(len(answer)):
        if guess[int] == answer[int]:   #filters words with correct letter at specific location
            # print(guess[int], "at specific location")
            return_list = filter(guess[int], position=(int), wordList=return_list)
        elif guess[int] in answer:    #filters words with correct letter present
            # print(guess[int], "in word")
            return_list = filter(guess[int], wordList=return_list)   
            return_list = wrongPositionFilter(guess[int], int, wordList=return_list) 
        elif guess[int] not in answer:  #filters out words with invalid letter in word
            # print(guess[int], "not in word")
            return_list = inverseFilter(filterChar=guess[int], wordList=return_list)
    for char in guess:
        if not guess.count(char) > 1 or not answer.count(char) > 1:
            continue
        if guess.count(char) <= answer.count(char): # "beers" "peees"
            return_list = repetition_filter(char, guess.count(char), return_list, False)  # we know the answer has at least guess.count(char) characters
        else: # guess count > answer count
            return_list = repetition_filter(char, answer.count(char), return_list, True) # answer count has the exact correct occurences of char
    return return_list

def filter(filterChar, position="any", repetitions="any", wordList="none"): #general purpose filter, covers correct letters, repetitions, and letters present
    returnList = []
    if type(position) == int:
        if position < 0 or position > 4:
            raise RuntimeError("InvalidCharacterPosition")
    if wordList == "none":
        available_words = open("words.txt", "r")
        wordList = [word for word in available_words]
        available_words.close()
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

def inverseFilter(filterChar, wordList="none"): #returns a list of words that do NOT contain the filter character
    returnList = []
    if wordList == "none":
        file = open("words.txt", "r")
        wordList = [line for line in file]
        file.close()
    for word in wordList:
        if filterChar not in word:
            returnList.append(word)
    return returnList

def wrongPositionFilter(filterChar, index, wordList="none"):    #returns a list of words that do not have the filter character at the specified index
    returnList = []
    if wordList == "none":
        file = open("words.txt", "r")
        wordList = [line for line in file]
        file.close()
    for word in wordList:
        if filterChar != word[index]:
            returnList.append(word)
    return returnList

def word_state_repetition_filter(word, wordState, word_list):  #filters out words with incorrect number of character repetitions using a word state
    # 1 identify repetitions in word
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

def get_word_value(word, letter_dictionary, counted_word=""):   #gets the word value based off of the frequency of the letters in the letter dictionary
    value = 0
    counted_letters = [letter for letter in counted_word]
    for letter in word:
        if letter not in counted_letters:
            value += letter_dictionary[letter]
            counted_letters.append(letter)
    return value

def isBlimp(wordList):   #returns whether or not a word list has the "blimp problem"
    if len(wordList) > 10 or len(wordList) < 3:
        return False
    threshold = math.floor(len(wordList)/2)
    commonLettersDict = {}
    for word1 in wordList:
        for word2 in wordList:
            if word2 == word1:
                continue
            if len(list(set(word1) & set(word2))) >= 3: # if words have at least 3 letters in common
                commonLetters = ""
                for letters in list(set(word1) & set(word2)):
                    commonLetters += letters
                commonLetters = "".join(sorted(commonLetters))
                try:
                    commonLettersDict[commonLetters] += 1
                    if commonLettersDict[commonLetters] >= threshold:
                        return True
                except:
                    commonLettersDict[commonLetters] = 1
    return False
    

def getBlimpMax(wordList, commonLetters, totalWords=wordsAllowed): #returns highest word by letter frequency, excluding letters in common with most possible answers
    letterDictionary = get_letter_dictionary(wordList)
    wordValues = {word:get_word_value(word, letterDictionary, commonLetters) for word in totalWords}
    return max(wordValues, key=wordValues.get)

def blimpSearch(wordList):  #made to avoid the "blimp problem" where a search would be narrowed down best by a word already filtered out
    """
    Chooses the next guess when the 'blimp' condition is met (small list
    of very similar words). Uses a Minimax strategy to find the guess
    that minimizes the size of the largest possible remaining word list
    in the worst-case scenario.
    """
    best_guess = ""
    # Initialize with a value larger than any possible list size
    min_max_remaining_size = len(wordList) + 1

    # Decide which set of words to try as guesses. Using all allowed words
    # is more thorough but slower. Using just the current candidates is faster.
    # Using wordsAllowed is generally better for breaking blimp situations.
    candidate_guesses = wordsAllowed

    if not candidate_guesses: # Safety check if wordsAllowed is somehow empty
        return getMaxValue1(wordList) # Fallback

    for candidate in candidate_guesses:
        max_remaining_size = 0
        # Keep track of outcomes if needed for tie-breaking based on average size
        # possible_outcome_sizes = []

        # Simulate guessing 'candidate' against each word currently possible
        for potential_answer in wordList:
            # Use a copy of wordList for the simulation to avoid modifying the original list
            simulated_remaining_list = filter_words(wordList[:], candidate, potential_answer)
            outcome_size = len(simulated_remaining_list)

            # Track the worst-case (largest) remaining list size for this candidate guess
            if outcome_size > max_remaining_size:
                max_remaining_size = outcome_size

            # possible_outcome_sizes.append(outcome_size) # Store size for avg calculation if needed

        # --- Score the candidate guess based on the worst-case outcome ---
        # If this candidate guarantees a smaller worst-case list than the current best, it's the new best.
        if max_remaining_size < min_max_remaining_size:
            min_max_remaining_size = max_remaining_size
            best_guess = candidate
            # avg_for_best = sum(possible_outcome_sizes) / len(possible_outcome_sizes) # Store avg if needed for tie-break

        # --- Tie-breaking logic (optional but helpful) ---
        elif max_remaining_size == min_max_remaining_size:
            # Prefer guesses that are still possible answers themselves
            if best_guess not in wordList and candidate in wordList:
                best_guess = candidate
                # avg_for_best = sum(possible_outcome_sizes) / len(possible_outcome_sizes) # Update avg
            # # Alternative tie-breaker: prefer lower average outcome size
            # else:
            #     current_avg = sum(possible_outcome_sizes) / len(possible_outcome_sizes)
            #     if current_avg < avg_for_best:
            #         best_guess = candidate
            #         avg_for_best = current_avg

    # --- Fallback ---
    # If no suitable guess was found (e.g., all guesses lead to the same large list,
    # which shouldn't happen with correct logic but is a safe fallback),
    # or if the best guess somehow remained empty.
    if not best_guess:
        print("Warning: BlimpSearch fallback triggered.") # Optional warning
        # Use a simple strategy like highest frequency on the remaining list
        best_guess = getMaxValue1(wordList)
        # Or even pick randomly from the list if getMaxValue1 fails
        if not best_guess and wordList:
             best_guess = random.choice(wordList)

    return best_guess

def get_word_value2(word, reset_list):   #goes through all the combinations of letter states for the word and returns a score based on the weighted average list reduction (lower is better)
    word_list = reset_list
    resulting_words_list_lengths = []
    lettersInWord = []
    for first_letter in range(3):
        for second_letter in range(3):
            for third_letter in range(3):
                for fourth_letter in range(3):
                    for fifth_letter in range(3):
                        if first_letter == 0:
                            word_list = inverseFilter(word[0], word_list)
                        elif first_letter == 1:
                            word_list = filter(word[0], wordList=word_list)
                            word_list = wrongPositionFilter(word[0], 0, word_list)
                            lettersInWord.append(word[0])
                        elif first_letter == 2:
                            word_list = filter(word[0], position=0, wordList=word_list)
                            lettersInWord.append(word[0])
                        if second_letter == 0:
                            if word[1] not in lettersInWord:
                                word_list = inverseFilter(word[1], word_list)
                        elif second_letter == 1:
                            word_list = filter(word[1], wordList=word_list)
                            word_list = wrongPositionFilter(word[1], 1, word_list)
                            lettersInWord.append(word[1])
                        elif second_letter == 2:
                            word_list = filter(word[1], position=1, wordList=word_list)
                            lettersInWord.append(word[1])
                        if third_letter == 0:
                            if word[2] not in lettersInWord:
                                word_list = inverseFilter(word[2], word_list)
                        elif third_letter == 1:
                            word_list = filter(word[2], wordList=word_list)
                            word_list = wrongPositionFilter(word[2], 2, word_list)
                            lettersInWord.append(word[2])
                        elif third_letter == 2:
                            word_list = filter(word[2], position=2, wordList=word_list)
                            lettersInWord.append(word[2])
                        if fourth_letter == 0:
                            if word[3] not in lettersInWord:
                                word_list = inverseFilter(word[3], word_list)
                        elif fourth_letter == 1:
                            word_list = filter(word[3], wordList=word_list)
                            word_list = wrongPositionFilter(word[3], 3, word_list)
                            lettersInWord.append(word[3])
                        elif fourth_letter == 2:
                            word_list = filter(word[3], position=3, wordList=word_list)
                            lettersInWord.append(word[3])
                        if fifth_letter == 0:
                            if word[4] not in lettersInWord:
                                word_list = inverseFilter(word[4], word_list)
                        elif fifth_letter == 1:
                            word_list = filter(word[4], wordList=word_list)
                            word_list = wrongPositionFilter(word[3], 3, word_list)
                            lettersInWord.append(word[4])
                        elif fifth_letter == 2:
                            word_list = filter(word[4], position=4, wordList=word_list)
                            lettersInWord.append(word[4])
                        wordState = str(first_letter) + str(second_letter) + str(third_letter) + str(fourth_letter) + str(fifth_letter)
                        if len(set(list(word))) != len(word):
                            word_list = word_state_repetition_filter(word, wordState, word_list)
                        # print("Testing word state", first_letter * 81 + second_letter * 27 + third_letter * 9 + fourth_letter * 3 + fifth_letter * 1)
                        # print(word, wordState, word_list)
                        if len(word_list) > 0:
                            resulting_words_list_lengths.append(0 - (len(reset_list) - len(word_list)) * get_list_matches(word, word_list, reset_list)) # made this negative so I didn't have to rewrite code
                        # print(resulting_words_list_lengths)
                        word_list = reset_list
    # print(word, weighted_value, resulting_words_list_lengths)
    if len(resulting_words_list_lengths) > 0:
        return sum(resulting_words_list_lengths) / len(reset_list)    #returns sum of weighted averages
    else:
        return 1   #returns 1 if there are no resulting word lists (all states are impossible to reach)

def get_list_matches(input_word, focused_list, main_list):    #iterates through the main list and returns the number of filtered lists from the main list that match the focused list
    reset_list = [word for word in main_list]
    matches = 0
    for word in main_list:
        main_list = filter_words(main_list, input_word, word)
        if main_list == focused_list:
            matches += 1
            # print("Matches found:", matches)
        main_list = reset_list
    # print(matches / len(main_list))
    return matches

def get_best_next_multithread(word_pool, totalWordList):    #multithreading-compatible method to get candidates for the best next word by weighted highest reduction average
    global min_word_dict
    minimum = get_word_value2(word_pool[0], totalWordList)
    min_word = word_pool[0]
    while len(word_pool) != 0:
        word = word_pool[0]
        # print("Testing word: " + word + "\n")
        word_value = get_word_value2(word, totalWordList)
        if word_value != 1 and word_value < min_word_dict[min(min_word_dict, key=min_word_dict.get)]:
            minimum = word_value
            min_word = word
        word_pool.remove(word)
    min_word_dict.update({min_word: minimum})

def chunks(list, n):
    """Yield successive n-sized chunks from list."""
    for i in range(0, len(list), n):
        yield list[i:i + n]

class Thread(threading.Thread): #custom thread class
   def __init__(self, targetMethod, name, wordList, totalWordList):
      threading.Thread.__init__(self)
      self.targetMethod = targetMethod
      self.name = name
      self.wordList = wordList
      self.totalWordList = totalWordList
   def run(self):
    #   print("Starting " + self.name + "\n")
      self.targetMethod(self.wordList, self.totalWordList)
    #   print("Exiting " + self.name + "\n")

def getMaxValue1(wordList): #returns highest word by letter frequency
    letterDictionary = get_letter_dictionary(wordList)
    wordValues = {word:get_word_value(word, letterDictionary) for word in wordList}
    return max(wordValues, key=wordValues.get)

def runMultithreadedHRBFR2(wordList, numberOfThreads):   #gets the next best word by highest reduction, using multithreading
    global min_word_dict
    baseThreads = threading.active_count()
    min_word_dict = {"zzzzz": 9999}
    wordListList = []
    wordListList.append([wordList[i:i + math.ceil(len(wordList) / numberOfThreads)] for i in range(0, len(wordList), math.ceil(len(wordList) / numberOfThreads))])
    if len(wordListList[0]) < numberOfThreads:
        r = len(wordListList[0])
    else:
        r = numberOfThreads
    threads = [Thread(get_best_next_multithread, "Thread " + str(i + 1), wordListList[0][i], wordList) for i in range(r)]
    for thread in threads:
        thread.start()
    while(1):
        if threading.active_count() == baseThreads:
            break
    if len(min_word_dict) > 1:  # returns the word with the lowest score out of all the local minimums
        # print(min_word_dict)
        best_word_list = []
        min_value = min_word_dict[min(min_word_dict, key=min_word_dict.get)]
        # print(min_value)
        for word in min_word_dict.keys():
            if min_word_dict[word] == min_value:        
                best_word_list.append(word)
        best_word = getMaxValue1(best_word_list)
        # print(best_word, best_word_list)
    else:
        best_word = min(min_word_dict, key=min_word_dict.get)
    return best_word

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

def test_MultiThreadedHRBFR2(n):    #tests deep search by highest weighted average list reduction
    game_data = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "DNF": 0}
    for i in range(n):
        available_words = [i[:-1] for i in open("words.txt", "r").readlines()]
        test_word = random.choice(available_words)
        steps = 1
        if test_word == "salet":
            print(steps, available_words)
            game_data.update({str(steps): game_data[str(steps)] + 1})
            success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
            print("MT_HRBFR2", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))
            continue
        available_words = filter_words(available_words, "salet", test_word)
        if test_word not in available_words:
            raise RuntimeError("Answer not in list")
        if len(available_words) == 1 and available_words[0] == test_word:
            steps += 1
            # print(steps, available_words)
            game_data.update({str(steps): game_data[str(steps)] + 1})
            success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
            print("MT_HRBFR2", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))
            continue
        for j in range(5):
            if isBlimp(available_words):
                guess = blimpSearch(available_words)
            else:
                if available_words == gameFilter("salet", "00000", permanent_answers):  #hard-coded second guesses based on testing
                    guess = "muddy"
                elif available_words == gameFilter("salet", "10000", permanent_answers):
                    guess = "hussy"
                elif available_words == gameFilter("salet", "01000", permanent_answers):
                    guess = "croak"
                elif available_words == gameFilter("salet", "00100", permanent_answers):
                    guess = "grill"
                elif available_words == gameFilter("salet", "00010", permanent_answers):
                    guess = "pique"
                elif available_words == gameFilter("salet", "00001", permanent_answers):
                    guess = "booth"
                else:
                    guess = runMultithreadedHRBFR2(available_words, len(available_words))
            available_words = filter_words(available_words, guess, test_word)
            steps += 1
            # print(steps, available_words)
            if test_word not in available_words:
                raise RuntimeError("Answer not in list")
            if len(available_words) == 1 and guess == test_word:
                game_data.update({str(steps): game_data[str(steps)] + 1})
                success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
                print("MT_HRBFR2", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))
                break 
            elif len(available_words) == 1 and available_words[0] == test_word:
                steps += 1
                if steps == 7:
                    game_data.update({"DNF": game_data["DNF"] + 1})
                    success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
                    print("MT_HRBFR2", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))
                    break
                else:
                    game_data.update({str(steps): game_data[str(steps)] + 1})
                    success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
                    print("MT_HRBFR2", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))
                    break    
        else:
            game_data.update({"DNF": game_data["DNF"] + 1})
            success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
            print("MT_HRBFR2", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))

# test_MultiThreadedHRBFR2(100)

def getMaxDeepSearch(available_words):
    if available_words == gameFilter("salet", "00000", permanent_answers):  #hard-coded second guesses based on testing
        guess = "muddy"
    elif available_words == gameFilter("salet", "10000", permanent_answers):
        guess = "hussy"
    elif available_words == gameFilter("salet", "01000", permanent_answers):
        guess = "croak"
    elif available_words == gameFilter("salet", "00100", permanent_answers):
        guess = "grill"
    elif available_words == gameFilter("salet", "00010", permanent_answers):
        guess = "pique"
    elif available_words == gameFilter("salet", "00001", permanent_answers):
        guess = "booth"
    else:
        guess = runMultithreadedHRBFR2(available_words, len(available_words))
    return guess

def validState(wordState):  #returns whether or not a word state is valid
    if len(wordState) != 5:
        return False
    else:
        try:
            for char in wordState:
                if int(char) < 0 or int(char) > 2:
                    return False
        except:
            return False
    return True

def gameSim(wordList=available_words):  #simulates a real game
    for i in range(6):
        word = input("Enter word: ")
        wordState = input("Enter word state: ")
        while not validState(wordState):
            word = input("Enter word: ")
            wordState = input("Enter word state: ")
        wordList = gameFilter(word, wordState, wordList)
        print(runMultithreadedHRBFR2(wordList, len(wordList)))
        gameStatus = input("Complete? (y/N): ")
        if gameStatus == 'Y' or gameStatus == 'y':
            break

# gameSim()
# --- ADD THIS FULLY MODIFIED FUNCTION ---
def test_highestFrequency(n):   # tests search using letter frequencies - NOW WITH VERBOSE OUTPUT + COLORS
    print(f"\n--- Starting Verbose Test Run ({n} games) ---")
    game_data = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "DNF": 0}

    # Reload lists each time for consistency if running multiple tests
    global available_words, permanent_answers, wordsAllowed
    available_words = [i[:-1] for i in open("words.txt", "r").readlines()]
    permanent_answers = [i[:-1] for i in open("words.txt", "r").readlines()]
    wordsAllowed = [i[:-1] for i in open("wordsAllowed.txt", "r").readlines()]

    for i in range(n):
        print(f"\n--- Game {i+1} ---")
        current_available_words = permanent_answers[:] # Use a copy for each game
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
            continue # Go to the next game

        current_available_words = filter_words(current_available_words, guessWord, test_word)
        print(f"  Remaining possible words: {len(current_available_words)}")
        if test_word not in current_available_words and len(current_available_words) > 0:
             print(f"  ***Warning: Target word '{test_word}' was filtered out!***")

        # --- Subsequent Guesses ---
        solved = False
        for j in range(5): # Max 5 more guesses
            if not current_available_words:
                print("  ***Error: No possible words left!***")
                steps = 7 # Mark as DNF
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
                break # Exit inner loop, go to next game

            current_available_words = filter_words(current_available_words, guessWord, test_word)
            print(f"  Remaining possible words: {len(current_available_words)}")
            if test_word not in current_available_words and len(current_available_words) > 0:
                print(f"  ***Warning: Target word '{test_word}' was filtered out!***")

        # --- Game End Check ---
        if not solved and steps <= 6:
             print(f"Failed unexpectedly before 6 guesses.")
             game_data.update({"DNF": game_data["DNF"] + 1})
        elif not solved and steps > 6:
             print(f"Failed to solve in 6 steps.")
             game_data.update({"DNF": game_data["DNF"] + 1})

        print(f"Guess History for game {i+1}: {guess_history}")

    # --- Final Stats ---
    print("\n--- Overall Results ---")
    total_games = sum(game_data.values())
    success_count = total_games - game_data["DNF"]
    success_rate = (success_count / total_games) if total_games > 0 else 0
    avg_steps = game_data_avg(game_data) # Use the existing function

    print(f"Method: highest_freq")
    print(f"Total Games Simulated: {total_games}")
    print(f"Results (Steps: Count): {game_data}")
    print(f"Success Rate: {success_rate:.4f}")
    print(f"Average Steps (for successful games): {avg_steps:.4f}")

# --- END OF MODIFIED FUNCTION ---

# def test_highestFrequency(n):   #tests search using letter frequencies
#     game_data = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "DNF": 0}
#     for i in range(n):
#         available_words = [i[:-1] for i in open("words.txt", "r").readlines()]
#         test_word = random.choice(available_words)
#         # print(test_word)
#         steps = 1
#         if test_word == "salet":
#             # print(steps, available_words)
#             game_data.update({str(steps): game_data[str(steps)] + 1})
#             success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
#             print("MT_HRBFR2", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))
#             continue
#         available_words = filter_words(available_words, "salet", test_word)
#         if test_word not in available_words:
#             raise RuntimeError("Answer not in list")
#         if len(available_words) == 1 and available_words[0] == test_word:
#             steps += 1
#             # print(steps, available_words)
#             game_data.update({str(steps): game_data[str(steps)] + 1})
#             success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
#             print("highest_freq", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))
#             continue
#         for j in range(5):
#             if isBlimp(available_words):
#                 guessWord = blimpSearch(available_words)
#             else:
#                 guessWord = getMaxValue1(available_words)
#             available_words = filter_words(available_words, guessWord, test_word)
#             steps += 1
#             # print(steps, available_words)
#             if test_word not in available_words:
#                 raise RuntimeError("Answer not in list")
#             if len(available_words) == 1 and guessWord == test_word:
#                 game_data.update({str(steps): game_data[str(steps)] + 1})
#                 success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
#                 print("highest_freq", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))
#                 break 
#             elif len(available_words) == 1 and available_words[0] == test_word:
#                 steps += 1
#                 if steps == 7:
#                     game_data.update({"DNF": game_data["DNF"] + 1})
#                     success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
#                     print("highest_freq", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))
#                     break
#                 else:
#                     game_data.update({str(steps): game_data[str(steps)] + 1})
#                     success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
#                     print("highest_freq", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))
#                     break       
#         else:
#             game_data.update({"DNF": game_data["DNF"] + 1})
#             success_rate = 1 - (game_data["DNF"] / (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]))
#             print("highest_freq", (game_data["1"] + game_data["2"] + game_data["3"] + game_data["4"] + game_data["5"] + game_data["6"] + game_data["DNF"]), game_data, success_rate, game_data_avg(game_data))
            
# test_highestFrequency(1000)

def get_guess_colors(guess, target_word):
    """
    Compares a guess to the target word and returns a string representing
    Wordle colors (G=Green, Y=Yellow, B=Black/Gray).
    Handles duplicate letters correctly.
    """
    if len(guess) != 5 or len(target_word) != 5:
        return "Error" # Should not happen

    colors = [''] * 5  # Initialize with placeholders
    target_list = list(target_word) # Mutable list to track used letters

    # First pass for Greens (Exact Matches)
    for i in range(5):
        if guess[i] == target_list[i]:
            colors[i] = 'G'
            target_list[i] = None # Mark this letter as used for green

    # Second pass for Yellows (Present but Wrong Position)
    for i in range(5):
        if colors[i] == '': # Only check letters not already marked Green
            if guess[i] in target_list:
                colors[i] = 'Y'
                # Mark the *first* available instance of this letter in target as used
                target_list[target_list.index(guess[i])] = None
            else:
                # If not Green or Yellow, it must be Black/Gray
                colors[i] = 'B'

    return "".join(colors) # Return as a single string like "BGYBB"

def format_colors_to_emoji(color_string):
    """Converts a color string like 'BGYBB' to emojis."""
    emoji_map = {'B': GRAY, 'G': GREEN, 'Y': YELLOW}
    # Use .get(char, char) to safely handle any unexpected characters
    return "".join(emoji_map.get(char, char) for char in color_string)