import codecs
import json

count = 0

with open('patents.json') as fp:
    patents = json.load(fp);
    for patent in patents:
        order_date = None
        dates = patent.get('dates')
        if dates.get('Grant'):
            order_date = dates.get('Grant')
        else:
            order_date = dates.get('Publication')

        filename = "patent-{:03d}.md".format(count)

        with codecs.open(filename, "w", 'utf-8') as output:
            output.write(u'---\n')
            output.write(u'layout: page\n')
            output.write(u'date: {}\n'.format(order_date))
            output.write(u'title: {}\n'.format(patent.get('title').strip()))
            for t in dates:
                output.write(u"{}: {}\n".format(t.lower(), dates[t]))
            output.write(u'---\n')

            output.write(patent.get('abstract').strip())
            count += 1
