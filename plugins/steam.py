from util import hook, http, web, text
import re

# this is still beta code. some things will be improved later.

steamcalc_url = "http://steamcalculator.com/id/{}/{}"
count_re = re.compile(r"Found (.*?) Games with a value of ")
region = "us"  # if you change this shit breaks


def db_init(db):
    "check to see that our db has the the top steam users table."
    db.execute("create table if not exists steam_rankings(id, value, count, "
                 "primary key(id))")
    db.commit()


@hook.command
def steamcalc(inp, db=None):
    "steamcalc <user> -- Check the value of <user>s steam account."
    db_init(db)

    if " " in inp:
        return "Invalid Steam ID"

    uid = inp.strip().lower()
    url = steamcalc_url.format(http.quote_plus(uid), region)

    # get the web page
    try:
        page = http.get_html(url)
    except Exception as e:
        return "Could not get Steam game listing: {}".format(e)

    # extract the info we need
    try:
        count_textual = page.xpath("//div[@id='rightdetail']/text()")[0]
        count = int(count_re.findall(count_textual)[0])

        value_textual = page.xpath("//div[@id='rightdetail']/h1/text()")[0]
        value = float(value_textual[1:][:-4])  # todo: make this less shit
    except IndexError:
        return "Could not get Steam game listing."

    # save the info in the DB for steam rankings
    db.execute("insert or replace into steam_rankings(id, value, count)"
            "values(?,?,?)", (uid, value, count))
    db.commit()

    # shorten the URL
    try:
        short_url = web.isgd(url)
    except web.ShortenError as e:
        short_url = url

    return u"Found {} games with a total value of ${} USD! - {}".format(count, value, short_url)


@hook.command(autohelp=False)
def steamtop(inp, db=None):
    "steamtop -- Shows the top five users from steamcalc."
    rows = []
    for row in db.execute("SELECT id, value, count FROM steam_rankings ORDER BY value DESC LIMIT 5"):
        rows.append(u"{} - \x02${}\x02 ({} games)".format(text.munge(row[0], 1), row[1], row[2]))

    return u"Top Steam Users: {}".format(", ".join(rows))
