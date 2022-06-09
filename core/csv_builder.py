import csv
from io import TextIOWrapper
from typing import Dict, List


class CSVBuilder:
    '''
    a helper to take a CSV file and add new data via columns and rows.
    requires knowledge of all headers before building
    usage:

    builder = CSVBuilder('~/input.csv', '~/output.csv')
    builder.add_headers(['new column 1', 'new column 2'])

    with builder:
        for row in builder.input_reader:
            new_data = {
                'new column 1': 'new data for col 1',
                'new column 2': 'new data for col 2'
            }
            builder.append_data(row, new_data)
    
    '''


    def __init__(self, input_file_path, output_file_path, input_encoding='utf-8-sig', output_encoding='utf-8') -> None:
        self.output_file_path = output_file_path
        self.output_encoding = output_encoding

        self.output_created: bool = False

        self.input_file_path = input_file_path
        self.input_encoding = input_encoding

        self.input_file: TextIOWrapper = None
        self.input_reader: csv.DictReader = None

        self._headers: List[str] = None
        with open(self.input_file_path, encoding=self.input_encoding, mode="r") as input_file:
            self.input_reader = csv.DictReader(input_file)
            self._headers = self.input_reader.fieldnames or []


    def __enter__(self):
        print("--- Entering `With` Mode ---")
        self.input_file = open(self.input_file_path, encoding=self.input_encoding, mode="r")
        self.input_reader = csv.DictReader(self.input_file)
    
    def __exit__(self, *exc):
        print("--- Closing Input File ---")
        self.input_file.close()
        
    def add_headers(self, headers: List[str]) -> None:
        if type(headers) is not list:
            raise ValueError("Must supply a list")

        self._headers.extend([h for h in headers if h not in self._headers])
    
    def create_output_file(self) -> bool:
        ''' create the output file with all added headers and return status of creation'''
        if not self._headers:
            print("No headers for output")
            return False

        try:
            with open(self.output_file_path, 'w', encoding=self.output_encoding) as output_file:
                output_writer = csv.DictWriter(output_file, self._headers, extrasaction="ignore")
                output_writer.writeheader()
                self.output_created = True
            
            return self.output_created
        except FileExistsError:
            print("File already Exists")
            return False
        finally:
            return False

    def append_data(self, row: Dict[str, str], new_data: Dict[str, str], escape_new_lines=True) -> None:
        if not self.output_created:
            self.create_output_file()
            
        if escape_new_lines:
            escaped_data = {}
            for k, v in new_data.items():
                escaped_data[k] = str(v).replace('\r\n', '\n').replace('\n', '\\n')
            
            new_data = escaped_data

        row.update(new_data)
        
        with open(self.output_file_path, 'a', encoding=self.output_encoding) as output_file:
            output_writer = csv.DictWriter(output_file, self._headers, extrasaction="ignore")
            output_writer.writerow(row)


