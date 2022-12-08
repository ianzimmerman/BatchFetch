import argparse
from core.apis.semrush import SEMRushQuery 


def main():
    '''
    python keyword.py "keyword" --api_key=XXXXXXXXXXXXXXXXXXX
    
    '''
    parser = argparse.ArgumentParser(description='''
            learn about a keyword
        ''')
    # parser.add_argument('i', metavar='i', type=str, help='input csv')
    parser.add_argument('k', metavar='k', type=str, help='keyword')
    args = parser.parse_args()

    semrush = SEMRushQuery()
    semrush.request_volume(args.k)

    print(semrush.response.content)


if __name__ == "__main__":
    main()