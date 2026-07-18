import tkinter as tk
import random

import pseudo_wording as ps


class WordGame(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Pseudoword Game")
        self.geometry("600x250")
        self.configure(bg="white")

        self.score = 0
        self.round = 0
        self.display_time = 50
        self.flash_time = 500
        self.answers = []

        self.main_label = tk.Label(
            self, text="Guess if the word is real or fake", font=("Arial", 28), bg="white"
        )
        self.main_label.pack(pady=20)

        self.score_label = tk.Label(
            self, text="There are 20 rounds", font=("Arial", 11), bg="white"
        )
        self.score_label.pack()

        self.button_frame = tk.Frame(self, bg="white")
        self.button_frame.pack(pady=20)

        self.start_button = tk.Button(
            self.button_frame,
            text="Start",
            command=lambda: self.start(),
            width=30,
            height=3,
            font=("Arial", 10)
        )
        self.start_button.grid(row=0, column=0, padx=10)

        self.time_button = tk.Button(
            self.button_frame,
            text="50ms",
            command=lambda: self.toggle_time(),
            width=30,
            height=3,
            font=("Arial", 10)
        )
        self.time_button.grid(row=0, column=1, padx=10)

        self.pseudo_button = tk.Button(
            self.button_frame,
            text="Pseudo",
            command=lambda: self.answer("pseudo"),
            width=30,
            height=3,
            font=("Arial", 10)
        )

        self.real_button = tk.Button(
            self.button_frame,
            text="Real",
            command=lambda: self.answer("real"),
            width=30,
            height=3,
            font=("Arial", 10)
        )

        with open("words_lib\mit\words.txt", "r", encoding="utf8") as file:
            self.real_words = [word.strip() for word in file.read().splitlines() if len(word) >= 5]

        self.mit_pwg = ps.PseudoWordGenerator("mit", False)
        self.woorm_pwg = ps.PseudoWordGenerator("woorm", False)

        self.mit_pwg.load_matrix(2)
        self.woorm_pwg.load_matrix(2)

    def toggle_time(self):
        match self.display_time:
            case 20:
                self.display_time = 30

            case 30:
                self.display_time = 50

            case 50:
                self.display_time = 100

            case 100:
                self.display_time = 200

            case 200:
                self.display_time = 20

        self.time_button.config(text=f"{self.display_time}ms")


    def start(self):
        self.score = 0
        self.round = 0

        self.start_button.grid_forget()
        self.time_button.grid_forget()
        self.pseudo_button.grid(row=0, column=0, padx=10)
        self.real_button.grid(row=0, column=1, padx=10)

        self.score_label.config(text=f"Score: {self.score}\t Round: {self.round + 1}")

        self.answers = []

        for i in range(20):
            word = ""
            if random.choice([True, False]):
                word_is_real = True
                word = random.choice(self.real_words)

            else:
                word_is_real = False

                while True:
                    if random.choice([True, False]):
                        word = "".join(self.mit_pwg.gen_tokenized_word(degree=2))[2:-2]

                    else:
                        word = "".join(self.woorm_pwg.gen_tokenized_word(degree=2))[2:-2]

                    if not word in self.real_words and 5 <= len(word) <= 13 and not word[:-1] in self.real_words:
                        break

            print(f"was real: {word_is_real}, word: {word}")
            self.answers.append((word, word_is_real))

        self.next_round()

    def next_round(self):
        self.configure(bg="white")
        self.main_label.configure(bg="white")
        self.score_label.configure(bg="white")

        self.main_label.config(text=self.answers[self.round][0])

        self.after_idle(
            lambda: self.after(
                self.display_time + (50 if self.round == 0 else 0),
                self.after_flash
            )
        )

    def after_flash(self):
        self.main_label.config(text="")

    def answer(self, chosen):
        if ((chosen == "real" and self.answers[self.round][1])
                or (chosen == "pseudo" and not self.answers[self.round][1])):
            self.score += 1
            self.flash("green")
        else:
            self.score -= 1
            self.flash("red")

        self.score_label.config(text=f"Score: {self.score}\t Round: {self.round + 1}")

        if self.round >= 19:
            self.after(self.flash_time, self.end_game)

        else:
            self.round += 1
            self.after(self.flash_time, self.next_round)

    def end_game(self):
        self.configure(bg="white")
        self.main_label.configure(bg="white", text="Guess if the word is real or fake")
        self.score_label.configure(bg="white")

        self.pseudo_button.grid_forget()
        self.real_button.grid_forget()
        self.start_button.grid(row=0, column=0, padx=10)
        self.time_button.grid(row=0, column=1, padx=10)

    def flash(self, color):
        self.configure(bg=color)
        self.main_label.configure(bg=color)
        self.score_label.configure(bg=color)


if __name__ == "__main__":
    app = WordGame()
    app.mainloop()
