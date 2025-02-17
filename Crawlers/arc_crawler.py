import scrapy
import unicodedata
import pandas as pd

class BlogSpider(scrapy.Spider):
    name = 'narutoplotspider'
    start_urls = ['https://naruto.fandom.com/wiki/Plot_of_Naruto']

    def normalize_text(self, text):
        """Normalize Unicode characters and strip extra spaces."""
        if text:
            text = unicodedata.normalize('NFKD', text)  # Normalize Unicode characters
            text = text.encode('ascii', 'ignore').decode('utf-8')  # Remove non-ASCII characters
            return text.strip()
        return ""

    def parse(self, response):
        tables = response.css('table.wikitable')
        
        if tables:
            table = tables[0]  # Assuming the first table
            rows = table.css('tbody tr')
            extracted_data = []

            for row in rows:
                cells = row.css('td, th')
                cell_texts = [self.normalize_text(cell.css('::text').get(default='')) for cell in cells]

                if cell_texts:  # Avoid empty rows
                    extracted_data.append(cell_texts)

            # Convert the extracted data into a Pandas DataFrame (assuming the first row is the header)
            df = pd.DataFrame(extracted_data[1:], columns=extracted_data[0])

            # Save to CSV (optional)
            df.to_csv('arc_table.csv', index=False, encoding='utf-8')