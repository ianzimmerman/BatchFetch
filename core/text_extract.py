from newspaper import Article
import nltk
import textstat
import math


class TextExtract:
    def __init__(self, url: str, update_punkt=False) -> None:
        if update_punkt:
            self.update_punkt()
        
        try:
            self.article = Article(url)
            self._html = self.article.download()
            self.article.parse()
            self.article.nlp()
        except:
            raise ConnectionError("Failed to download or parse URL.")
    
    @property
    def get_html(self):
        return self.article.html
    
    @staticmethod
    def update_punkt():
        nltk.download('punkt')

    @property
    def content_report(self):
        text = self.article.text
        if text:

            word_count = textstat.lexicon_count(text)
            sentence_count = textstat.sentence_count(text)
            dc_score = textstat.dale_chall_readability_score(text)
            fre_score = textstat.flesch_reading_ease(text)
            fk_grade = textstat.flesch_kincaid_grade(text)

            return {
                'Source Domain': self.article.source_url,
                'Keywords': ','.join(self.article.keywords),
                'Summary': self.article.summary.replace('\r\n','\n'),
                'Top Image':self.article.top_image,
                'Words': word_count,
                'Sentences': sentence_count,
                'Reading time (sec)': self._reading_time_in_seconds(text),
                'Reading time (min)': self._reading_time_in_minutes(text),
                'Dale/Chall Score': dc_score,
                'Dale/Chall Score Name': self._dale_chall_to_text(dc_score),
                'Flesch Reading Ease Score': fre_score,
                'Flesch Reading Ease Score Name': self._flesch_score_to_text(fre_score),
                'Flesch/Kincade Grade': fk_grade,
                'Flesch/Kincade Grade Name': self._kincade_to_text(fk_grade),
            }
        else:
            return {
                'Source URL': self.article.source_url
            }
    
    @staticmethod
    def headers():
        return [
            'Source Domain',
            'Keywords',
            'Summary',
            'Top Image',
            'Words',
            'Sentences',
            'Reading time (sec)',
            'Reading time (min)',
            'Dale/Chall Score',
            'Dale/Chall Score Name',
            'Flesch Reading Ease Score',
            'Flesch Reading Ease Score Name',
            'Flesch/Kincade Grade',
            'Flesch/Kincade Grade Name',
        ]
    
    def _reading_time_in_seconds(self, text: str, wpm=200) -> int:
        wc = textstat.lexicon_count(text)
        decimal_minutes = round(wc/wpm, 3)
        mins = math.floor(decimal_minutes)
        secs = (decimal_minutes - mins)*60

        return math.floor((mins*60) + secs)

    def _reading_time_in_minutes(self, text: str, wpm=200, rounding=True) -> float:
        secs = self._reading_time_in_seconds(text, wpm)
        if rounding:
            return round(secs/60)
        else:
            return secs/60
    
    def _flesch_score_to_text(self, f_score: int) -> str:
        score_map = {
            'Very Easy': 90,
            'Easy': 80,
            'Fairly Easy': 70,
            'Standard': 60,
            'Fairly Difficult': 50,
            'Difficult': 30,
            'Very Difficult': 0
        }

        for name, score in score_map.items():
            if f_score >= score:
                return name

        return 'N/A'
    
    def _dale_chall_to_text(self, dc_score: float) -> str:
        score_map = [
            ('13th to 15th-grade student', 9.0, 9.9),
            ('11th or 12th-grade student', 8.0, 8.9),
            ('9th or 10th-grade student', 7.0, 7.9),
            ('7th or 8th-grade student', 6.0, 6.9),
            ('5th or 6th-grade student', 5.0, 5.9),
            ('4th-grade student or lower', 0, 4.9),
        ]

        for name, min, max in score_map:
            if dc_score >= min:
                return name

        return 'N/A'
    
    def _kincade_to_text(self, k_score: float) -> str:
        score_map = [
            (100.00, 90.00, '5th grade'),
            (90.0, 80.0, '6th grade'),
            (80.0, 70.0, '7th grade'),
            (70.0, 60.0, '8th & 9th grade'),
            (60.0, 50.0, '10th to 12th grade'),
            (50.0, 30.0, 'Some College'),
            (30.0, 10.0, 'College graduate'),
            (10.0, 0.0, 'Professional')
        ]

        for max, min, name in score_map:
            if k_score >= min:
                return name

        return 'N/A'

