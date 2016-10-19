import json

count = 0

with open('patents.json') as fp:
    patents = json.load(fp);
    for patent in patents:
        order_date = None
        dates = patent.get('dates')
        if dates.get('Granted'):
            order_date = dates.get('Granted')
        else:
            order_date = dates.get('Publication')

        print "{:03d}".format(count)
        print '---'
        print 'layout: patent'
        print 'abstract: ' + patent.get('abstract').strip()
        print 'title: ' + patent.get('title').strip()
        print 'date: ' + order_date
        for t in dates:
            print "{}: {}".format(t.lower(), dates[t])
        print '---'
        count += 1
