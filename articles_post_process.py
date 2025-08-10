print("Loading article list....")
with open("articles.txt", "r+") as articles:
    article_list = articles.readlines()

allowed_articles = []
i = 0
m = str(len(article_list))
for article in article_list:
    i += 1
    print(str(i) + "/" + m)
    if article.isascii():
        allowed_articles.append(article)

print("Writing new list...")
with open("articles_processed.txt", "w+") as processed:
    processed.writelines(allowed_articles)
