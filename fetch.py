import argparse
import csv
import time
from typing import Dict

from core.apis.semrush import SEMRushQuery
from core.csv_builder import CSVBuilder
from core.html_reader import HTMLReader
from core.text_extract import TextExtract


def main():
    '''
    python fetch.py /path/to/input.csv -c url -f project_name --api_key=XXXXXXXXXXXXXXXXXXX
    
    '''
    parser = argparse.ArgumentParser(description='''
            automate things with a csv of URLs
        ''')

    parser.add_argument('i', metavar='i', type=str, help='input csv')
    parser.add_argument('-c', type=str, help='which column contains the URI', default='location')
    parser.add_argument('-f', type=str, help='filename prefix', default='all_data')

    parser.add_argument('--api_key', metavar='api_key', type=str, help='apikey')

    args = parser.parse_args()

    timestr = time.strftime("%Y%m%d-%H%M%S")
    output_file = f'output_files/{args.f}_all_results_{timestr}.csv'

    builder = CSVBuilder(args.i, output_file_path=output_file)
    builder.add_headers(HTMLReader.csv_headers())
    builder.add_headers(['Est. Monthly SEO Traffic', 'Top SEO Keywords'])
    builder.add_headers(TextExtract.headers())

    kw_output_file = f'output_files/{args.f}_keyword_results_{timestr}.csv'
    keyword_file = open(kw_output_file, mode="w", encoding="utf-8")
    keyword_writer = csv.DictWriter(keyword_file, SEMRushQuery.headers(), extrasaction='ignore')
    keyword_writer.writeheader()
    
    with builder:
        for i, row in enumerate(builder.input_reader):
            uri = row.get(args.c)
            if uri == None or uri.startswith('http') == False:
                continue
            
            new_data: Dict[str, str] = dict()
            results = {}

            try:
                text_extactor = TextExtract(uri, update_punkt=(i==0))
                new_data.update(text_extactor.content_report)
                results['text'] = "Success"
            except Exception as e:
                results['text'] = f"Failed: {e}"

            print(i+1, uri)
            print("    Text Extract: ", results['text'])

            try:
                html_reader = HTMLReader(uri)
                new_data.update(html_reader.csv_report)
                results['meta'] = "Success"
            except Exception as e:
                results['meta'] = f"Failed: {e}"
            
            print("    Meta Extract: ", results['meta'])
            
            q = SEMRushQuery(args.api_key)
            q.add_filter("+", "Po", "Lt", 21)
            
            q.request(uri, limit=25)
            
            seo_data = {
                'Est. Monthly SEO Traffic': 0,
                'Top SEO Keywords': ''
            }

            seo_keywords = []
            for r in q.results:
                keyword_writer.writerow(r.dict())
                seo_data['Est. Monthly SEO Traffic'] += r.et
                if r.tr > 4.9:
                    seo_keywords.append(r.ph)
            
            seo_data['Top SEO Keywords'] = ', '.join(seo_keywords)

            print("    SEO Results: ", f" Keywords: {len(q.results)}, Est. Traffic: {seo_data['Est. Monthly SEO Traffic']}")

            new_data.update(seo_data)
            
            builder.append_data(row, new_data)

    keyword_file.close()

if __name__ == "__main__":
    main()
