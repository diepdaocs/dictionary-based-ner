from langdetect import detect
import pandas as pd


def main():
    cities = set()
    with open('cities15000.txt') as f:
        for idx, line in enumerate(f.readlines()):
            print 'Processing line %s' % idx
            elements = line.split('\t')
            alias1 = elements[1].strip().lower() if elements[1] and len(elements) > 0 else None
            alias2 = elements[2].strip().lower() if elements[2] and len(elements) > 1 else None
            list_alias = [t.strip().lower() for t in elements[3].split(',') if t and t.strip()] if elements[3] and len(elements) > 2 else []
            if alias1:
                cities.add(alias1)
            if alias2:
                cities.add(alias2)

            for alias in list_alias:
                if alias and detect_lang(alias) == 'en':
                    cities.add(alias)

    df = pd.DataFrame()
    df['vocabulary'] = list(cities)
    df.to_csv('cities15000_en.out.csv', index=False, encoding='utf-8')
    pass


def detect_lang(text):
    try:
        return detect(text)
    except:
        return None


if __name__ == '__main__':
    main()
