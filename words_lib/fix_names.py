from os import path


with open("names.txt", "r", encoding="utf8") as n_file:
    with open(path.join("female_names", "words.txt"), "w", encoding="utf8") as f_file:
        with open(path.join("male_names", "words.txt"), "w", encoding="utf8") as m_file:
            for line in n_file:
                name, gender = line.lower().split(" ")

                if "m" in gender:
                    m_file.write(f"{name}\n")

                elif "f" in gender:
                    f_file.write(f"{name}\n")
