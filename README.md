# EngAnalysis
This repo is consists of two maint parts: the pseudo-English generator and the Wikipedia scraper. The latter was made to scrape through Wikipedia articles and make a database record of most common English letters, words, and phonemes. The former uses a Markov-chain based method to generate plausible-seeming English words; as well as sentences and paragraphs.

## Entry Points
- To run the Wikipedia scraping component, run `wiki_scraper.py`. The scraper runs in the terminal, with a Tkinter visualization popup.
- To run the component that generates pseudo-English, run `pseudo_word_gen.py`. Run the HELP action in the CLI to get an understanding of how to use, or alternatively, import it as a Python module in code.
- To see if you can discern between the real and fake, play the game in `pseudo_game.py`. Note that if you set the visibility time to the lower options Tkinter sometimes doesn't redraw fast enough and it won't be shown.

## Licensing
The words.txt file in each source of the words_lib directory are compiled from sources not my own.
