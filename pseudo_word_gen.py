import pickle
import random
import textwrap
import tqdm

from util import *
from colorama import Fore, Style

from words_lib import tokenizer
from pos import get_poss, contextify_word
from phon import get_ipa
from text_gen import gen_paragraph


colorama.init(autoreset=True)


class MarkovMatrix:
    """
    Strictly set dimension defaulting dictionary
    """
    def __init__(self, degree: int, default, matrix: dict = None):
        self.degree = degree
        self.default = default
        self._matrix = dict() if matrix is None else matrix

    def __repr__(self) -> str:
        return f"MarkovMatrix({self.degree}, {self.default})"

    def __str__(self) -> str:
        return str(self._matrix)

    def __setitem__(self, keys, value):
        self.__getitem__.cache_clear()

        if len(keys) == self.degree + 1:
            self._matrix[keys] = value

        else:
            raise KeyError("keys not of matrix dimension")

    @lru_cache(maxsize=100000)
    def __getitem__(self, keys, tokens: tuple = None):
        if len(keys) < self.degree + 1:
            if tokens:
                return {
                    **{ token: 0 for token in tokens },
                    **{ key[-1]: val for key, val in self._matrix.items() if key[:len(keys)] == keys }
                }

            else:
                return {
                    key[-1]: val for key, val in self._matrix.items() if key[:len(keys)] == keys
                }

        elif len(keys) == self.degree + 1:
            try:
                return self._matrix[keys]

            except KeyError:
                return self.default

        else:
            raise KeyError("matrix keys out of range")

    @staticmethod
    def load(file):
        return MarkovMatrix(*pickle.load(file))

    def dump(self, file):
        pickle.dump(
            (self.degree, self.default, self._matrix), file
        )


class PseudoWordGenerator:
    RAINBOW_COLORS = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    START_TOKEN = "<"
    END_TOKEN = ">"

    def __init__(self, source: str, verbose: bool = False, reset: bool = False):
        self.source = path.join("words_lib", source)
        self.reset = reset

        self.verbose = verbose
        self.color_i = 0

        self.words = Words(self.source)
        self.matrices = {}

        self.vprint("tokenizing...", end="")
        self.tokens = tokenizer.generate_tokens(self.words, self.source, self.reset)
        self.vprint(f" {Fore.GREEN}complete{Fore.RESET}")
        self.vprint(f"tokens: {Fore.YELLOW}{', '.join(self.tokens)}{Fore.RESET}")
        self.vprint(f"there are {Fore.YELLOW}{len(self.tokens)}{Fore.RESET} tokens")
        self.vprint()

    def __repr__(self) -> str:
        return f"PseudoWordGenerator({self.source}, {self.verbose}, {self.reset})"

    def __str__(self) -> str:
        return str(self.matrices)

    def _find_subsequent_token(self, text: str, i: int) -> list:
        text = text[i:]
        found_token = ""
        max_token_len = 0

        for token in self.tokens:
            if text[:len(token)] == token and len(token) > max_token_len:
                found_token = token
                max_token_len = len(token)

        return found_token

    def _find_subsequent_tokens(self, text: str, i: int) -> list:
        text = text[i:]
        found_tokens = []

        for token in self.tokens:
            if text[:len(token)] == token:
                found_tokens.append(token)

        return found_tokens

    def load_matrix(self, top_degree: int, reset: bool = False):
        for degree in range(1, top_degree + 1):
            if not self.matrices.get(degree, False):
                matrix_path = path.join(self.source, f"matrix.d{degree}.pkl")

                if reset or not path.exists(matrix_path):
                    self.vprint(f"building matrix.d{degree}...", end="")
                    self.build_matrix(degree)

                    with open(matrix_path, "wb") as file:
                        self.matrices[degree].dump(file)

                else:
                    self.vprint(f"loading matrix.d{degree}...", end="")

                    with open(matrix_path, "rb") as file:
                        self.matrices[degree] = MarkovMatrix.load(file)

                clean_matrix = str(self.matrices[degree]).replace("'", "")[:100]
                self.vprint(f" {Fore.GREEN}complete{Fore.RESET}")
                self.vprint(f"matrix.d{degree} head: {Fore.YELLOW}{clean_matrix}...{Fore.RESET}")
                self.vprint()

    def build_matrix(self, degree: int):
        self.matrices[degree] = MarkovMatrix(degree, 0)

        print()
        for word, freq_count in tqdm(self.words):
            word = self.START_TOKEN * degree + word.strip() + self.END_TOKEN * degree

            for pre_token in self.tokens:
                for pre_token_i in find_all_substrings(word, pre_token):
                    token_key = [pre_token]

                    for token_count in range(degree):
                        pre_token_i += len(token_key[token_count])

                        next_token = self._find_subsequent_token(word, pre_token_i)

                        if next_token:
                            token_key.append(next_token)

                        else:
                            # At the end of the word, no need to keep looking
                            # As _tokens contains the whole alphabet we can be sure that any word is tokenizeable
                            break

                    else:
                        # This runs when len(token_key) == degree + 1, because it completed without breaking
                        assert len(token_key) == degree + 1
                        self.matrices[degree][tuple(token_key)] += freq_count

    def gen_next_token(
            self, context: list, has_vowel: bool, degree: int, temperature: int, chaos: int, disallow_end: bool = False,
            a: float = 0.1, b: float = 0.3
    ):
        """chaos is from 0 to 100 (percentage) and represents how much deviance is allowed from true values"""
        token_count = len(context)
        current_word = "".join(context)

        # Get choice matrix for next token
        keys = []

        for scope in range(-degree, 0):
            keys.append(
                default_get(context, scope, "<")
            )

        matrix = self.matrices[degree].__getitem__(tuple(keys), self.tokens)
        matrix_keys = list(matrix.keys())
        end_token_index = matrix_keys.index(self.END_TOKEN)
        weights = list(matrix.values())

        if token_count < degree:
            return self.START_TOKEN

        # Make ending the word more likely as it gets longer
        if disallow_end:
            weights[end_token_index] = 0

        else:
            weights[end_token_index] *= 1 + a * (token_count ** (1 + (token_count * b)))

        if chaos:
            total_weight = sum(weights)
            variance = max(int(total_weight * chaos // 100), 1)

            if variance != 0:
                for w in range(len(weights) - 2):
                    weights[2 + w] = max(0, weights[2 + w] + random.randrange(-variance, variance))

            new_weight = sum(weights)

            # approximate reconciliation for diminishing the proportion of end_token weight
            if (diff := new_weight - total_weight) > 0:
                weights[end_token_index] += diff // 2

        continuing_chance = sum(weights) - weights[end_token_index]

        if continuing_chance == 0:
            # If there are no options recurse down to lower context matrix or randomize if already at lowest
            if degree == 1:
                weights[2 + random.randrange(len(weights) - 2)] = 1

            else:
                return self.gen_next_token(context, has_vowel, degree - 1, temperature, chaos, disallow_end, a, b)

        retry = True
        attempt = 0
        next_token = None

        while True:
            if next_token is not None:
                if next_token == self.END_TOKEN:
                    if len(current_word) == 0 and not has_vowel:
                        retry = True

                    elif disallow_end:
                        retry = True

                # Disallow three of the same letter or more in a row
                elif current_word[-2:] == next_token[0] * 2:
                    retry = True

                if len(next_token) == 1:
                    # If last two letters aren't vowels and last letter of word is next_token
                    if not contains_vowel(current_word[-2:-1]) and current_word[-1:] == next_token[0]:
                        retry = True
                else:
                    # If last letter is consonant and next two letters are the same
                    if not contains_vowel(current_word[-1:]) and next_token[0] == next_token[1]:
                        retry = True

            # If fails to make good word 50 times, then just make a bad word
            if retry and not attempt > 50:
                next_token = random.choice(
                    random.choices(
                        population=matrix_keys,
                        weights=weights,
                        k=temperature
                    )
                )

                if next_token == self.END_TOKEN and len(current_word) - degree < 6 and not random.randint(0, 2):
                    # Start a new sub-word
                    return self.gen_next_token(
                        [self.START_TOKEN] * degree, has_vowel, degree, temperature, chaos, disallow_end, a, b
                    )

                attempt += 1
            else:
                break

        return next_token

    def gen_tokenized_word(self, degree: int = 1, temperature: int = 1, chaos: int = 0) -> list:
        word = [self.START_TOKEN] * degree
        has_vowel = False

        while word[-1] != self.END_TOKEN:
            next_token = self.gen_next_token(
                word, has_vowel, degree, temperature, chaos, False, 0.032, 0.63
            )

            word.append(next_token)

            if contains_vowel(next_token):
                has_vowel = True

        word = word + [self.END_TOKEN] * (degree - 1)

        if not has_vowel and len(word) > degree + 2:
            return self.gen_tokenized_word(temperature, chaos)

        return word

    def gen_full_word(self, degree: int = 1, temperature: int = 1, chaos: int = 0) -> tuple[str, str]:
        self.load_matrix(degree)

        return self.gen_word_metadata(self.gen_tokenized_word(degree, temperature, chaos))

    def gen_word_metadata(self, tokenized_word):
        word = "".join(tokenized_word)
        short_word = word[degree:-degree]
        printable_poss, poss = get_poss(short_word)
        ipa = get_ipa(short_word)

        self.vprint(
            f"{Fore.RESET}  {Style.BRIGHT}{short_word}{Style.RESET_ALL} "
            f"({Fore.YELLOW}{printable_poss}{Fore.RESET}) "
            f"/{Fore.CYAN}{ipa}{Fore.RESET}/",
            end = ""
        )

        self.vprint(f" [{self.get_colorized_tokens(tokenized_word)}{Fore.RESET}]", flush=True)

        example_sentence = contextify_word(short_word, max(poss, key=poss.get))

        stylized_example_sentence = textwrap.fill(
            example_sentence, width=50
        ).replace("\n", "\n     \"")

        self.vprint(f'     "{stylized_example_sentence} \n')

        with open(path.join(self.source, "log.txt"), "a", encoding="utf8") as log:
            log.write(f"\n{word} ({printable_poss}) /{ipa}/ [{'|'.join(tokenized_word)}] \"{example_sentence}\"")

        return short_word, poss

    def get_colorized_tokens(self, tokens) -> str:
        colorized_text = ""

        for token in tokens:
            colorized_text += self.RAINBOW_COLORS[self.color_i % len(self.RAINBOW_COLORS)] + token
            self.color_i += 1

        return colorized_text

    def tokenize(self, text: str) -> list:
        tokens = []
        i = 0

        while i < len(text):
            next_token = None

            for token in self.tokens:
                if (next_token is None or len(token) > len(next_token)) and text[i:i + len(token)] == token:
                    next_token = token

            tokens.append(next_token)
            i += len(next_token)

        return tokens


    def vprint(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)


def default_get(iterable, index, default):
    try:
        return iterable[index]

    except IndexError:
        return default


def contains_vowel(text: str) -> bool:
    return any(vowel in text for vowel in tokenizer.VOWELS)


def request(text: str, default, cast: type):
    print(f"{Fore.RESET}{text}> {Fore.MAGENTA}", end="", flush=True)

    try:
        answer = cast(input() or default)
        print(Fore.RESET, end="", flush=True)
        return answer

    except ValueError:
        return default

    except KeyboardInterrupt:
        print(f"\n{Fore.GREEN}session terminated\n{Fore.RESET}", flush=True)
        exit()


def print_man():
    print(
        f"\n"
        f"There are five available actions. You need not write a command's name in full though,\n"
        f"just the first letter will suffice. For each prompt that you are given, if you reply\n"
        f"with nothing (by pressing ENTER) it will just use the default value or the value that\n"
        f"you last supplied for that prompt. Parameters are given by name, then type, and then\n"
        f"their default value.\n"
        f"  {Fore.MAGENTA}HELP{Fore.RESET}\n"
        f"         Opens up this page.\n"
        f"  {Fore.MAGENTA}MATRIX{Fore.RESET}\n"
        f"         Uses the tokenized Markov-chain to generate usually fake, yet plausible,\n"
        f"         English words. Also generates an IPA pronunciation, its part of speech,\n"
        f"         an sentence illustrating example usage, and its token buildup.\n"
        f"     :{Fore.YELLOW}degree{Fore.RESET} [{Fore.CYAN}int{Fore.RESET}] = 1 :\n"
        f"         This is the number of tokens that are seen in the lookback of all the\n"
        f"         algorithms. It seems that 4 is overfit and 1 is a little too random, yet\n"
        f"         more interesting that 4. 2 or 3 is the sweet spot.\n"
        f"     :{Fore.YELLOW}number of words{Fore.RESET} [{Fore.CYAN}int{Fore.RESET}] = 10 :\n"
        f"         How many word entries will be generated in this run.\n"
        f"     :{Fore.YELLOW}temperature{Fore.RESET} [{Fore.CYAN}int{Fore.RESET}] = 1 :\n"
        f"         The number of possible next tokens that are generated at each step, of which\n"
        f"         only one is actually chosen. Can improve results.\n"
        f"     :{Fore.YELLOW}chaos{Fore.RESET} [{Fore.CYAN}int{Fore.RESET}] = 0 :\n"
        f"         A percentage from 0 to 100 that represents a deviance from the normal\n"
        f"         probability values when generating the next token. It can lead to poor\n"
        f"         results, and I do not recommend.\n"
        f"  {Fore.MAGENTA}SENTENCE{Fore.RESET}\n"
        f"         Generates a single sentence, using the previous batch of words generated by\n"
        f"         the matrix command as part of the vocabulary.\n"
        f"     :{Fore.YELLOW}vocab words{Fore.RESET} [{Fore.CYAN}str{Fore.RESET}]:\n"
        f"         If there are no previous words, you must supply your own vocabulary. Separate\n"
        f"         each word by a space.\n"
        f"  {Fore.MAGENTA}PARAGRAPH{Fore.RESET}\n"
        f"         Generates a multi-sentence paragraph, using the previous batch of words\n"
        f"         generated by the matrix command as part of the vocabulary.\n"
        f"     :{Fore.YELLOW}vocab words{Fore.RESET} [{Fore.CYAN}str{Fore.RESET}]:\n"
        f"         If there are no previous words, you must supply your own vocabulary. Separate\n"
        f"         each word by a space.\n"
        f"     :{Fore.YELLOW}number of sentences{Fore.RESET} [{Fore.CYAN}int{Fore.RESET}] = 5...10 :\n"
        f"         If you supply zero, or leave this argument as its default, the paragraph will\n"
        f"         generate with a random number between 5 and 10 sentences. Otherwise, it will\n"
        f"         have the number of sentences that you specify.\n"
        f"  {Fore.MAGENTA}CONTINUE{Fore.RESET}\n"
        f"         Takes the start of a word as context and then generates more tokens on the end\n"
        f"         of it. The command automatically prepends the START_TOKEN, so do not do so\n"
        f"         manually. Once it has finished it will also generate the other metadata.\n"
        f"     :{Fore.YELLOW}degree{Fore.RESET} [{Fore.CYAN}int{Fore.RESET}] = 1 :\n"
        f"         Same as for the matrix command.\n"
        f"     :{Fore.YELLOW}context{Fore.RESET} [{Fore.CYAN}str{Fore.RESET}] = '' :\n"
        f"         The text to use as context; the start of a word.\n"
        f"     :{Fore.YELLOW}tokens{Fore.RESET} [{Fore.CYAN}int{Fore.RESET}] = 1 :\n"
        f"         The maximum number of non-END_TOKEN tokens that will be appended. If the\n"
        f"         algorithm reaches an END_TOKEN before this number it will stop early.\n"
        f"     :{Fore.YELLOW}disallow early end{Fore.RESET} [{Fore.CYAN}bool{Fore.RESET}] = True :\n"
        f"         Prevents the algorithm from ending word early.\n"
        f"     :{Fore.YELLOW}temperature{Fore.RESET} [{Fore.CYAN}int{Fore.RESET}] = 1 :\n"
        f"         Same as for the matrix command.\n"
        f"     :{Fore.YELLOW}chaos{Fore.RESET} [{Fore.CYAN}int{Fore.RESET}] = 0 :\n"
        f"         Same as for the matrix command.\n"
    )


if __name__ == "__main__":
    # possibles sources: words_alpha, mit, woorm, big, male_names, female_names
    model = PseudoWordGenerator("words_alpha", True, False)

    degree = 1
    temperature = 1
    chaos = 0
    num_words = 10
    disallow_end = False
    prev_words = []

    print(f"Run the {Fore.MAGENTA}HELP{Fore.RESET} action for an explanation.")

    # io loop
    r = 0

    while True:
        action = request("action", "m", str).lower()

        if action == "help"[:len(action)]:
            print_man()

        elif action == "paragraph"[:len(action)]:
            if prev_words:
                vocab_words = prev_words

            else:
                vocab_words = input("vocab words").strip().split()

            if (num_sentences := request("number of sentences", 0, int)) == 0:
                print(f"{Fore.YELLOW}{gen_paragraph(random.randrange(5, 10), vocab_words)}")

            else:
                print(f"{Fore.YELLOW}{gen_paragraph(num_sentences, vocab_words, True)}")

        elif action == "sentence"[:len(action)]:
            if prev_words:
                vocab_words = prev_words

            else:
                vocab_words = input("vocab words").strip().split()

            print(f"{Fore.YELLOW}{gen_paragraph(1, vocab_words, True)}")

        elif action == "matrix"[:len(action)] or action == "_":
            prev_words = []

            if action != "_":
                degree = request("degree", degree, int)
                num_words = request("number of words", num_words, int)
                temperature = request("temperature", temperature, int)
                chaos = request("chaos", chaos, int)

            for _ in range(num_words):
                word, poss = model.gen_full_word(degree, temperature, chaos)

                for pos in poss:
                    prev_words.append((word, pos.capitalize() if pos != "adjective" else "Adj"))

        elif action == "continue"[:len(action)]:
            degree = request("degree", degree, int)
            context = [model.START_TOKEN] * degree + model.tokenize(
                request("context", "", str).strip(model.START_TOKEN).strip(model.END_TOKEN)
            )
            tokens = request("tokens", 1, int)
            disallow_end = False if request("disallow early end", disallow_end, str).lower() in ("0", "no", "false", "f") else True
            temperature = request("temperature", temperature, int)
            chaos = request("chaos", chaos, int)

            i = 0
            while context[-1] != model.END_TOKEN:
                model.load_matrix(degree)

                context += model.gen_next_token(
                    context, contains_vowel("".join(context)), degree, temperature, chaos,
                    i <= tokens if disallow_end else True
                )

                print(f" {i + 1}) {model.get_colorized_tokens(context)}")
                i += 1

            context = context + [model.END_TOKEN] * (degree - 1)
            model.gen_word_metadata(context)

        print()
